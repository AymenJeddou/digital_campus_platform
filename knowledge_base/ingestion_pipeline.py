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
from app.services.course_ingestion import _chunk_text
from app.services.text_extraction import extract_text

logger = logging.getLogger(__name__)


def ingest_document_pipeline(document_id: str):
    """Extract -> chunk -> embed -> store a Document as global KB chunks.
    New chunks are embedded before the old ones are dropped (one commit), so a
    failed re-ingest leaves the previous version searchable."""
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            logger.error("Document %s not found for ingestion.", document_id)
            return

        text = doc.content or ""
        if doc.file_path:
            with open(doc.file_path, "rb") as fh:
                text = extract_text(doc.title, fh.read())

        chunks = _chunk_text(text, source=doc.title, title=doc.title) if text.strip() else []
        embeddings = []
        if chunks:
            from ai.rag.embeddings import embed_texts
            embeddings = embed_texts([c["text"] for c in chunks], batch_size=32)

        db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).delete()
        db.add_all(
            DocumentChunk(
                document_id=doc.id,
                text=c["text"],
                title=doc.title,
                source=doc.title,
                page=c.get("page", 0),
                category="knowledge_base",  # global KB, not a course material
                embedding=embedding,
            )
            for c, embedding in zip(chunks, embeddings)
        )
        doc.is_ingested = True
        db.commit()
        logger.info("Document %s ingested: %d chunks.", document_id, len(chunks))
    except Exception:
        logger.exception("Ingestion failed for document %s", document_id)
        db.rollback()
    finally:
        db.close()
