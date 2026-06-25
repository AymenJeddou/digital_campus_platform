from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.dependencies import get_current_user
from app.models.models import Student, Document
from app.schemas.document import DocumentResponse
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/documents", tags=["Documents"])

class DocumentCreate(BaseModel):
    title: str
    content: Optional[str] = None

@router.get("", response_model=list[DocumentResponse])
def list_documents(db: Session = Depends(get_db), current_user: Student = Depends(get_current_user)):
    return db.query(Document).all()

@router.post("", response_model=DocumentResponse, status_code=201)
def upload_document(body: DocumentCreate, db: Session = Depends(get_db), current_user: Student = Depends(get_current_user)):
    doc = Document(title=body.title, content=body.content)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc
