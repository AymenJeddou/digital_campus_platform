from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.db.database import get_db, SessionLocal
from app.core.dependencies import get_current_user
from app.models.models import Student, ChatSession, ChatMessage, Feedback
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.feedback import FeedbackCreate, FeedbackResponse
from app.services.rag import generate_chat_response, generate_chat_response_stream
from sse_starlette.sse import EventSourceResponse
import uuid
import json

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("", response_model=ChatResponse)
def send_message(request: ChatRequest, db: Session = Depends(get_db), current_user: Student = Depends(get_current_user)):
    if request.session_id:
        session = db.query(ChatSession).filter(ChatSession.id == request.session_id).first()
        if not session or session.student_id != current_user.id:
            raise HTTPException(status_code=404, detail="Session not found")
    else:
        session = ChatSession(student_id=current_user.id)
        db.add(session)
        db.commit()
        db.refresh(session)

    user_message = ChatMessage(session_id=session.id, role="user", content=request.message)
    db.add(user_message)

    bot_reply = generate_chat_response(message=request.message, session_id=session.id, student=current_user)
    bot_message = ChatMessage(
        session_id=session.id, 
        role="assistant", 
        content=bot_reply["answer"], 
        citations=bot_reply["citations"]
    )
    db.add(bot_message)
    db.commit()

    return {"session_id": session.id, "answer": bot_reply["answer"], "citations": bot_reply["citations"]}

@router.post("/stream")
def send_message_stream(request: ChatRequest, db: Session = Depends(get_db), current_user: Student = Depends(get_current_user)):
    if request.session_id:
        session = db.query(ChatSession).filter(ChatSession.id == request.session_id).first()
        if not session or session.student_id != current_user.id:
            raise HTTPException(status_code=404, detail="Session not found")
    else:
        session = ChatSession(student_id=current_user.id)
        db.add(session)
        db.commit()
        db.refresh(session)

    user_message = ChatMessage(session_id=session.id, role="user", content=request.message)
    db.add(user_message)
    db.commit()

    stream, chunks = generate_chat_response_stream(message=request.message, session_id=session.id, student=current_user)
    session_id = session.id

    async def event_generator():
        full_answer = ""
        grounded = None
        for chunk in stream:
            # The pipeline ends a factual stream with a groundedness marker
            # ("\n\n[groundedness_check: True]"). Surface it as its own event and
            # keep it OUT of the answer text we display and persist.
            if chunk.startswith("\n\n[groundedness_check:"):
                grounded = "True" in chunk
                yield {"data": json.dumps({"grounded": grounded})}
                continue
            full_answer += chunk
            yield {"data": json.dumps({"chunk": chunk})}

        citations = []
        if chunks:
            from ai.rag.citation_formatter import format_citations
            formatted = format_citations(full_answer, chunks)
            citations = formatted.get("citations", [])
            yield {"data": json.dumps({"citations": citations})}

        # Persist with a fresh session: the request-scoped `db` may be closed by
        # the time this streaming generator finishes.
        save_db = SessionLocal()
        try:
            save_db.add(ChatMessage(
                session_id=session_id,
                role="assistant",
                content=full_answer,
                citations=citations,
            ))
            save_db.commit()
        finally:
            save_db.close()

        yield {"data": "[DONE]"}

    return EventSourceResponse(event_generator())

@router.post("/feedback", response_model=FeedbackResponse)
def submit_feedback(feedback: FeedbackCreate, db: Session = Depends(get_db), current_user: Student = Depends(get_current_user)):
    chat_msg = db.query(ChatMessage).filter(ChatMessage.id == feedback.chat_message_id).first()
    if not chat_msg:
        raise HTTPException(status_code=404, detail="Message not found")

    # IDOR guard: only let a user rate a message in a session they own.
    owned = db.query(ChatSession).filter(
        ChatSession.id == chat_msg.session_id,
        ChatSession.student_id == current_user.id,
    ).first()
    if not owned:
        raise HTTPException(status_code=404, detail="Message not found")

    new_feedback = Feedback(
        chat_message_id=feedback.chat_message_id,
        user_id=current_user.id,
        rating=feedback.rating,
        comment=feedback.comment
    )
    db.add(new_feedback)
    db.commit()
    db.refresh(new_feedback)
    return new_feedback

@router.get("/sessions")
def get_sessions(db: Session = Depends(get_db), current_user: Student = Depends(get_current_user)):
    return db.query(ChatSession).filter(ChatSession.student_id == current_user.id).all()

@router.get("/sessions/{session_id}/messages")
def get_messages(session_id: uuid.UUID, db: Session = Depends(get_db), current_user: Student = Depends(get_current_user)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session or session.student_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")
    return db.query(ChatMessage).filter(ChatMessage.session_id == session_id).all()
