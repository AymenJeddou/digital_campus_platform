"""Admin dashboard data: usage numbers, answer feedback, unanswered questions.

The thumbs-down list and the unanswered list are the raw material for the
eval set (knowledge_base/eval) and for deciding which documents to add.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ai.prompts.system_prompts import NO_INFO_SENTENCE
from app.core.dependencies import require_admin
from app.db.database import get_db
from app.models.models import ChatMessage, ChatSession, Document, Feedback, Student

router = APIRouter(prefix="/admin", tags=["Admin"], dependencies=[Depends(require_admin)])


def _question_for(db: Session, answer: ChatMessage) -> str | None:
    """The user message an assistant message answered."""
    question = (
        db.query(ChatMessage.content)
        .filter(
            ChatMessage.session_id == answer.session_id,
            ChatMessage.role == "user",
            ChatMessage.created_at <= answer.created_at,
        )
        .order_by(ChatMessage.created_at.desc())
        .first()
    )
    return question[0] if question else None


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    ratings = dict(db.query(Feedback.rating, func.count()).group_by(Feedback.rating).all())
    return {
        "students": db.query(func.count(Student.id)).scalar(),
        "conversations": db.query(func.count(ChatSession.id)).scalar(),
        "questions": db.query(func.count(ChatMessage.id)).filter(ChatMessage.role == "user").scalar(),
        "unanswered": db.query(func.count(ChatMessage.id)).filter(
            ChatMessage.role == "assistant", ChatMessage.content == NO_INFO_SENTENCE).scalar(),
        "flagged": db.query(func.count(ChatMessage.id)).filter(ChatMessage.grounded.is_(False)).scalar(),
        "helpful": ratings.get(1, 0),
        "not_helpful": ratings.get(0, 0),
        "documents": db.query(func.count(Document.id)).scalar(),
    }


@router.get("/feedback")
def feedback(rating: int | None = Query(None, ge=0, le=1), limit: int = Query(50, le=200), db: Session = Depends(get_db)):
    query = db.query(Feedback, ChatMessage).join(ChatMessage, ChatMessage.id == Feedback.chat_message_id)
    if rating is not None:
        query = query.filter(Feedback.rating == rating)
    rows = query.order_by(Feedback.timestamp.desc()).limit(limit).all()
    return [
        {
            "id": fb.id,
            "rating": fb.rating,
            "comment": fb.comment,
            "timestamp": fb.timestamp,
            "question": _question_for(db, message),
            "answer": message.content,
            "citations": message.citations or [],
        }
        for fb, message in rows
    ]


@router.get("/unanswered")
def unanswered(limit: int = Query(50, le=200), db: Session = Depends(get_db)):
    """Questions the assistant couldn't answer from the documents, newest first."""
    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.role == "assistant", ChatMessage.content == NO_INFO_SENTENCE)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
        .all()
    )
    return [{"id": m.id, "question": _question_for(db, m), "asked_at": m.created_at} for m in rows]
