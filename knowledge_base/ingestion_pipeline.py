"""Real ingestion for admin-uploaded knowledge-base documents.

Reads the uploaded file, extracts its text, chunks and embeds it, and stores the
result as GLOBAL knowledge-base chunks (student_id/course_id/material_id = NULL,
so they are visible to everyone). Reuses the same extraction/chunking/embedding
machinery as course-material ingestion.

Runs as a FastAPI BackgroundTask, so it takes its OWN DB session rather than
borrowing the request session (which is closed once the response is sent).
"""
import logging

from app.db.database import SessionLocal
from app.models.models import Document, DocumentChunk
from app.services.text_extraction import extract_text
from app.services.course_ingestion import _chunk_text

logger = logging.getLogger(__name__)


def ingest_document_pipeline(document_id: str):
    """Extract -> chunk -> embed -> store a Document as global KB chunks."""
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            logger.error("Document %s not found for ingestion.", document_id)
            return

        # Idempotency: drop any prior chunks for this document.
        db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).delete()
        db.commit()

        text = ""
        if doc.file_path:
            with open(doc.file_path, "rb") as fh:
                text = extract_text(doc.title, fh.read())
        elif doc.content:
            text = doc.content

        if not text or not text.strip():
            doc.is_ingested = True
            db.commit()
            logger.warning("Document %s had no extractable text.", document_id)
            return

        chunks = _chunk_text(text, source=doc.title, title=doc.title)
        if chunks:
            from ai.rag.embeddings import embed_texts
            embeddings = embed_texts([c["text"] for c in chunks], batch_size=32)
            db.bulk_save_objects([
                DocumentChunk(
                    document_id=doc.id,
                    text=c["text"],
                    title=c.get("title", doc.title),
                    source=c.get("source", doc.title),
                    page=c.get("page", 0),
                    category="knowledge_base",   # global KB, not a course material
                    embedding=embedding,
                    student_id=None,
                    course_id=None,
                    material_id=None,
                )
                for c, embedding in zip(chunks, embeddings)
            ])

        doc.is_ingested = True
        db.commit()
        logger.info("Document %s ingested: %d chunks.", document_id, len(chunks))
    except Exception:
        logger.exception("Ingestion failed for document %s", document_id)
        db.rollback()
    finally:
        db.close()
