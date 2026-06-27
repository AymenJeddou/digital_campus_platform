from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.dependencies import get_current_user
from app.models.models import Student, ChatSession, ChatMessage
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.rag import generate_chat_response
import uuid

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
    bot_message = ChatMessage(session_id=session.id, role="assistant", content=bot_reply["answer"])
    db.add(bot_message)
    db.commit()

    return {"session_id": session.id, "answer": bot_reply["answer"], "citations": bot_reply["citations"]}

@router.get("/sessions")
def get_sessions(db: Session = Depends(get_db), current_user: Student = Depends(get_current_user)):
    return db.query(ChatSession).filter(ChatSession.student_id == current_user.id).all()

@router.get("/sessions/{session_id}/messages")
def get_messages(session_id: uuid.UUID, db: Session = Depends(get_db), current_user: Student = Depends(get_current_user)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session or session.student_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")
    return db.query(ChatMessage).filter(ChatMessage.session_id == session_id).all()
