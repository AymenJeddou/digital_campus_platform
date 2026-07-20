from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.dependencies import get_current_user
from app.models.models import Student, Document
from app.schemas.document import DocumentResponse
import shutil
import os
import uuid
from knowledge_base.ingestion_pipeline import ingest_document_pipeline

router = APIRouter(prefix="/documents", tags=["Documents"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".txt", ".md"}

def require_admin_user(current_user: Student = Depends(get_current_user)) -> Student:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

@router.get("", response_model=list[DocumentResponse])
def list_documents(db: Session = Depends(get_db), current_user: Student = Depends(get_current_user)):
    return db.query(Document).all()

@router.post("/upload", response_model=DocumentResponse, status_code=201)
def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db), 
    current_user: Student = Depends(require_admin_user)
):
    # Never trust the client filename: it can contain path traversal
    # ("../../app/main.py"). Keep only the basename for display, and write to a
    # server-generated name so an upload can never escape UPLOAD_DIR.
    original_name = os.path.basename(file.filename or "upload")
    ext = os.path.splitext(original_name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type '{ext}'.")

    stored_name = f"{uuid.uuid4().hex}{ext}"
    file_location = os.path.join(UPLOAD_DIR, stored_name)
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)

    doc = Document(
        title=original_name,
        file_path=file_location,
        uploaded_by_id=current_user.id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Background task takes its own DB session (see ingestion_pipeline).
    background_tasks.add_task(ingest_document_pipeline, str(doc.id))

    return doc
