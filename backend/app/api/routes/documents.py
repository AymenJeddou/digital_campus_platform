"""Knowledge-base documents, managed by admins from the admin dashboard."""
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin
from app.db.database import get_db
from app.models.models import Document, DocumentChunk, Student
from app.schemas.document import DocumentResponse
from app.services.text_extraction import SUPPORTED_EXTENSIONS
from knowledge_base.ingestion_pipeline import ingest_document_pipeline

router = APIRouter(prefix="/documents", tags=["Documents"])

# backend/uploads, independent of the directory uvicorn was started from.
UPLOAD_DIR = Path(__file__).resolve().parents[3] / "uploads"
MAX_UPLOAD_BYTES = 20 * 1024 * 1024


@router.get("", response_model=list[DocumentResponse])
def list_documents(db: Session = Depends(get_db), admin: Student = Depends(require_admin)):
    rows = (
        db.query(Document, func.count(DocumentChunk.chunk_id))
        .outerjoin(DocumentChunk, DocumentChunk.document_id == Document.id)
        .group_by(Document.id)
        .order_by(Document.uploaded_at.desc())
        .all()
    )
    return [
        DocumentResponse.model_validate(doc).model_copy(update={"chunk_count": count})
        for doc, count in rows
    ]


@router.post("/upload", response_model=DocumentResponse, status_code=201)
def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: Student = Depends(require_admin),
):
    # Never trust the client filename (it can contain "../"): keep only the
    # basename for display and store under a server-generated name.
    original_name = os.path.basename(file.filename or "upload")
    ext = os.path.splitext(original_name)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=415, detail=f"Unsupported file type '{ext}'.")

    raw = file.file.read(MAX_UPLOAD_BYTES + 1)
    if not raw:
        raise HTTPException(status_code=422, detail="The uploaded file is empty")
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large — the limit is 20 MB.")

    UPLOAD_DIR.mkdir(exist_ok=True)
    file_location = UPLOAD_DIR / f"{uuid.uuid4().hex}{ext}"
    file_location.write_bytes(raw)

    doc = Document(title=original_name, file_path=str(file_location), uploaded_by_id=admin.id)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    # The background task opens its own DB session (see ingestion_pipeline).
    background_tasks.add_task(ingest_document_pipeline, str(doc.id))
    return doc


@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: uuid.UUID, db: Session = Depends(get_db), admin: Student = Depends(require_admin)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).delete()
    if doc.file_path and Path(doc.file_path).resolve().parent == UPLOAD_DIR:
        Path(doc.file_path).unlink(missing_ok=True)
    db.delete(doc)
    db.commit()
