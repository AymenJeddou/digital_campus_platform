"""Chunk, embed and store course materials."""
from __future__ import annotations

import logging
import uuid

from sqlalchemy.orm import Session

from app.models.models import CourseMaterial, DocumentChunk

logger = logging.getLogger(__name__)

TARGET_CHUNK_CHARS = 800


def delete_material_chunks(db: Session, material_id: uuid.UUID, commit: bool = True) -> None:
    """Delete all document chunks of a course material."""
    db.query(DocumentChunk).filter(DocumentChunk.material_id == material_id).delete()
    if commit:
        db.commit()


def _split(text: str, size: int = TARGET_CHUNK_CHARS) -> list[str]:
    """Pack paragraphs into ~``size``-char pieces. An oversized paragraph is
    split by line, and an oversized line by words."""
    pieces: list[str] = []
    current: list[str] = []
    length = 0

    def flush():
        nonlocal current, length
        if current:
            pieces.append("\n\n".join(current))
        current, length = [], 0

    for paragraph in (p.strip() for p in text.split("\n\n")):
        if not paragraph:
            continue
        if len(paragraph) <= size:
            if length + len(paragraph) + 2 > size:
                flush()
            current.append(paragraph)
            length += len(paragraph) + 2
            continue
        flush()
        for line in (l.strip() for l in paragraph.split("\n")):
            if len(line) <= size:
                if line:
                    pieces.append(line)
                continue
            words: list[str] = []
            for word in line.split(" "):
                if words and len(" ".join(words)) + len(word) + 1 > size:
                    pieces.append(" ".join(words))
                    words = []
                words.append(word)
            if words:
                pieces.append(" ".join(words))
    flush()
    return pieces or ([text.strip()] if text.strip() else [])


def _chunk_text(text: str, source: str, title: str) -> list[dict]:
    return [
        {"chunk_id": str(uuid.uuid4()), "text": piece, "title": title, "source": source,
         "page": 0, "category": "course_material"}
        for piece in _split(text)
    ]


def ingest_material(db: Session, material: CourseMaterial) -> None:
    """Chunk, embed and store a CourseMaterial. The new chunks are embedded
    BEFORE the old ones are removed, and the swap is one commit, so a failed
    re-ingest keeps the previous (still searchable) version."""
    try:
        source_name = material.original_filename or material.source
        chunks = _chunk_text(material.content or "", source_name, material.title)
        embeddings = []
        if chunks:
            from ai.rag.embeddings import embed_texts
            embeddings = embed_texts([c["text"] for c in chunks], batch_size=32)

        delete_material_chunks(db, material.id, commit=False)
        db.add_all(
            DocumentChunk(
                chunk_id=uuid.UUID(chunk["chunk_id"]) if _is_uuid(chunk["chunk_id"]) else uuid.uuid4(),
                document_id=None,
                text=chunk["text"],
                title=chunk.get("title", material.title),
                source=chunk.get("source", source_name),
                page=chunk.get("page", 0),
                category=chunk.get("category", "course_material"),
                embedding=embedding,
                student_id=material.student_id,
                course_id=material.course_id,
                material_id=material.id,
            )
            for chunk, embedding in zip(chunks, embeddings)
        )
        material.status = "ingested"
        material.chunk_count = len(chunks)
        material.error_message = None
        db.commit()
    except Exception as e:
        db.rollback()
        logger.exception("Ingestion failed for course material %s", material.id)
        material.status = "error"
        material.error_message = str(e)[:500]
        db.commit()


def _is_uuid(value) -> bool:
    try:
        uuid.UUID(str(value))
        return True
    except ValueError:
        return False
