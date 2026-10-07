import json
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from app.core import rate_limit
from app.core.dependencies import get_current_user
from app.db.database import SessionLocal, get_db
from app.models.models import ChatMessage, ChatSession, Feedback, Student, StudentCourse
from app.schemas.chat import ChatRequest, ChatResponse, MessageResponse, SessionResponse, SessionUpdate
from app.schemas.feedback import FeedbackCreate, FeedbackResponse
from app.services.rag import ERROR_MESSAGE, generate_chat_response, generate_chat_response_stream

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])

HISTORY_TURNS = 6
GROUNDEDNESS_MARKER = "\n\n[groundedness_check:"


async def chat_rate_limiter(current_user: Student = Depends(get_current_user)):
    """Every message costs LLM calls, so cap them per user."""
    await rate_limit.hit(f"chat:{current_user.id}", 20, 60, "Trop de messages. Attends une minute.")
    await rate_limit.hit(f"chat-day:{current_user.id}", 300, 86400, "Limite quotidienne de messages atteinte.")


def _now():
    return datetime.now(timezone.utc)


def _owned_session(db: Session, session_id, user: Student) -> ChatSession:
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session or session.student_id != user.id:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


def _history(db: Session, session_id, before=None) -> list[dict]:
    """The last turns of a session (oldest first), optionally only those
    created before a given time. Never includes the question being answered."""
    query = db.query(ChatMessage).filter(ChatMessage.session_id == session_id)
    if before is not None:
        query = query.filter(ChatMessage.created_at < before)
    rows = query.order_by(ChatMessage.created_at.desc()).limit(HISTORY_TURNS).all()
    return [{"role": m.role, "content": m.content} for m in reversed(rows)]


def _prepare(request: ChatRequest, db: Session, user: Student) -> tuple[ChatSession, str, list[dict]]:
    """Resolve the session, the question to answer and its history, and
    persist the user's message. Shared by the plain and streaming endpoints."""
    if request.course_id and not db.query(StudentCourse).filter(
        StudentCourse.student_id == user.id, StudentCourse.course_id == request.course_id
    ).first():
        raise HTTPException(status_code=403, detail="You are not enrolled in this course")

    if request.regenerate:
        if not request.session_id:
            raise HTTPException(status_code=422, detail="session_id is required to regenerate")
        session = _owned_session(db, request.session_id, user)
        last_question = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session.id, ChatMessage.role == "user")
            .order_by(ChatMessage.created_at.desc())
            .first()
        )
        if not last_question:
            raise HTTPException(status_code=400, detail="Nothing to regenerate")
        # Drop the answer(s) being replaced, and their feedback.
        stale = db.query(ChatMessage).filter(
            ChatMessage.session_id == session.id,
            ChatMessage.role == "assistant",
            ChatMessage.created_at > last_question.created_at,
        ).all()
        for message in stale:
            db.query(Feedback).filter(Feedback.chat_message_id == message.id).delete()
            db.delete(message)
        db.commit()
        return session, last_question.content, _history(db, session.id, before=last_question.created_at)

    question = request.message.strip()
    if not question:
        raise HTTPException(status_code=422, detail="Message is empty")
    if request.session_id:
        session = _owned_session(db, request.session_id, user)
    else:
        session = ChatSession(student_id=user.id, title=question[:80])
        db.add(session)
        db.flush()
    history = _history(db, session.id)
    db.add(ChatMessage(session_id=session.id, role="user", content=question))
    session.updated_at = _now()
    db.commit()
    return session, question, history


@router.post("", response_model=ChatResponse, dependencies=[Depends(chat_rate_limiter)])
def send_message(request: ChatRequest, db: Session = Depends(get_db), current_user: Student = Depends(get_current_user)):
    session, question, history = _prepare(request, db, current_user)
    reply = generate_chat_response(question, current_user, history, course_id=request.course_id)
    db.add(ChatMessage(session_id=session.id, role="assistant", content=reply["answer"], citations=reply["citations"]))
    db.commit()
    return {"session_id": session.id, "answer": reply["answer"], "citations": reply["citations"]}


@router.post("/stream", dependencies=[Depends(chat_rate_limiter)])
def send_message_stream(request: ChatRequest, db: Session = Depends(get_db), current_user: Student = Depends(get_current_user)):
    session, question, history = _prepare(request, db, current_user)
    stream, chunks = generate_chat_response_stream(question, current_user, history, course_id=request.course_id)
    session_id = session.id

    # A plain (sync) generator: sse-starlette runs it in a worker thread, so the
    # blocking LLM stream never stalls the event loop for other requests.
    def save(answer: str, citations: list, grounded) -> str:
        # Own session: the request-scoped one is closed by the time we get here.
        save_db = SessionLocal()
        try:
            message = ChatMessage(session_id=session_id, role="assistant", content=answer,
                                  citations=citations, grounded=grounded)
            save_db.add(message)
            save_db.commit()
            return str(message.id)
        finally:
            save_db.close()

    def event_generator():
        yield {"data": json.dumps({"session_id": str(session_id)})}
        answer, grounded, citations, saved = "", None, [], False
        try:
            try:
                for token in stream:
                    # The pipeline ends a factual answer with a groundedness marker;
                    # surface it as its own event, keep it out of the answer text.
                    if token.startswith(GROUNDEDNESS_MARKER):
                        grounded = "True" in token
                        yield {"data": json.dumps({"grounded": grounded})}
                        continue
                    answer += token
                    yield {"data": json.dumps({"chunk": token})}
                if chunks:
                    from ai.rag.citation_formatter import format_citations
                    citations = format_citations(answer, chunks).get("citations", [])
                    yield {"data": json.dumps({"citations": citations})}
            except Exception:
                logger.exception("Streaming failed mid-answer (session=%s)", session_id)
                if not answer:
                    answer = ERROR_MESSAGE
                    yield {"data": json.dumps({"chunk": ERROR_MESSAGE})}
            message_id = save(answer, citations, grounded)
            saved = True
            yield {"data": json.dumps({"message_id": message_id})}
            yield {"data": "[DONE]"}
        finally:
            # The client stopped the answer (generator closed early): keep
            # what was already said so the conversation stays coherent.
            if not saved and answer:
                save(answer, citations, grounded)

    return EventSourceResponse(event_generator())


@router.post("/feedback", response_model=FeedbackResponse)
def submit_feedback(feedback: FeedbackCreate, db: Session = Depends(get_db), current_user: Student = Depends(get_current_user)):
    message = db.query(ChatMessage).filter(ChatMessage.id == feedback.chat_message_id).first()
    # IDOR guard: only rate messages in your own sessions (404 either way).
    if not message or not db.query(ChatSession).filter(
        ChatSession.id == message.session_id, ChatSession.student_id == current_user.id
    ).first():
        raise HTTPException(status_code=404, detail="Message not found")

    existing = db.query(Feedback).filter(
        Feedback.chat_message_id == message.id, Feedback.user_id == current_user.id
    ).first()
    entry = existing or Feedback(chat_message_id=message.id, user_id=current_user.id)
    entry.rating = feedback.rating
    entry.comment = feedback.comment
    entry.timestamp = _now()
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/sessions", response_model=list[SessionResponse])
def get_sessions(db: Session = Depends(get_db), current_user: Student = Depends(get_current_user)):
    return (
        db.query(ChatSession)
        .filter(ChatSession.student_id == current_user.id)
        .order_by(ChatSession.updated_at.desc().nulls_last(), ChatSession.created_at.desc())
        .all()
    )


@router.patch("/sessions/{session_id}", response_model=SessionResponse)
def rename_session(session_id: uuid.UUID, body: SessionUpdate, db: Session = Depends(get_db), current_user: Student = Depends(get_current_user)):
    session = _owned_session(db, session_id, current_user)
    session.title = body.title.strip()
    db.commit()
    db.refresh(session)
    return session


@router.delete("/sessions/{session_id}", status_code=204)
def delete_session(session_id: uuid.UUID, db: Session = Depends(get_db), current_user: Student = Depends(get_current_user)):
    session = _owned_session(db, session_id, current_user)
    message_ids = [m.id for m in db.query(ChatMessage.id).filter(ChatMessage.session_id == session.id)]
    if message_ids:
        db.query(Feedback).filter(Feedback.chat_message_id.in_(message_ids)).delete(synchronize_session=False)
        db.query(ChatMessage).filter(ChatMessage.session_id == session.id).delete(synchronize_session=False)
    db.delete(session)
    db.commit()


@router.get("/sessions/{session_id}/messages", response_model=list[MessageResponse])
def get_messages(session_id: uuid.UUID, db: Session = Depends(get_db), current_user: Student = Depends(get_current_user)):
    _owned_session(db, session_id, current_user)
    rows = (
        db.query(ChatMessage, Feedback.rating)
        .outerjoin(Feedback, (Feedback.chat_message_id == ChatMessage.id) & (Feedback.user_id == current_user.id))
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
        .all()
    )
    return [
        MessageResponse.model_validate(message).model_copy(update={"rating": rating})
        for message, rating in rows
    ]
