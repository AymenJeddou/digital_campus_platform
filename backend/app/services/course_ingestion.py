"""Service for chunking and embedding course materials and storing them in the database.
"""
from __future__ import annotations

import logging
import uuid
from sqlalchemy.orm import Session

from app.models.models import CourseMaterial, DocumentChunk

logger = logging.getLogger(__name__)


def delete_material_chunks(db: Session, material_id: uuid.UUID) -> None:
    """Delete all document chunks associated with a course material."""
    db.query(DocumentChunk).filter(DocumentChunk.material_id == material_id).delete()
    db.commit()


def _chunk_text(text: str, source: str, title: str) -> list[dict]:
    """Chunk text into semantic paragraphs/segments."""
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = []
    current_length = 0
    page = 0
    target_size = 800

    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        if len(p) > target_size:
            if current_chunk:
                chunks.append({
                    "chunk_id": str(uuid.uuid4()),
                    "text": "\n\n".join(current_chunk),
                    "title": title,
                    "source": source,
                    "page": page,
                    "category": "course_material",
                })
                current_chunk = []
                current_length = 0

            lines = p.split("\n")
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if len(line) > target_size:
                    words = line.split(" ")
                    line_chunk = []
                    line_len = 0
                    for word in words:
                        if line_len + len(word) + 1 > target_size:
                            chunks.append({
                                "chunk_id": str(uuid.uuid4()),
                                "text": " ".join(line_chunk),
                                "title": title,
                                "source": source,
                                "page": page,
                                "category": "course_material",
                            })
                            line_chunk = [word]
                            line_len = len(word)
                        else:
                            line_chunk.append(word)
                            line_len += len(word) + 1
                    if line_chunk:
                        chunks.append({
                            "chunk_id": str(uuid.uuid4()),
                            "text": " ".join(line_chunk),
                            "title": title,
                            "source": source,
                            "page": page,
                            "category": "course_material",
                        })
                else:
                    chunks.append({
                        "chunk_id": str(uuid.uuid4()),
                        "text": line,
                        "title": title,
                        "source": source,
                        "page": page,
                        "category": "course_material",
                    })
        else:
            if current_length + len(p) + 2 > target_size:
                chunks.append({
                    "chunk_id": str(uuid.uuid4()),
                    "text": "\n\n".join(current_chunk),
                    "title": title,
                    "source": source,
                    "page": page,
                    "category": "course_material",
                })
                current_chunk = [p]
                current_length = len(p)
            else:
                current_chunk.append(p)
                current_length += len(p) + 2

    if current_chunk:
        chunks.append({
            "chunk_id": str(uuid.uuid4()),
            "text": "\n\n".join(current_chunk),
            "title": title,
            "source": source,
            "page": page,
            "category": "course_material",
        })

    if not chunks and text.strip():
        chunks.append({
            "chunk_id": str(uuid.uuid4()),
            "text": text.strip(),
            "title": title,
            "source": source,
            "page": page,
            "category": "course_material",
        })

    return chunks


def ingest_material(db: Session, material: CourseMaterial) -> None:
    """Chunk, embed, and store a CourseMaterial in the database."""
    try:
        # Delete old chunks to ensure idempotency
        delete_material_chunks(db, material.id)

        if not material.content or not material.content.strip():
            material.status = "ingested"
            material.chunk_count = 0
            db.commit()
            return

        # Chunk the text
        source_name = material.original_filename or material.source
        chunks = _chunk_text(material.content, source_name, material.title)

        if chunks:
            # Embed chunks
            from ai.rag.embeddings import embed_texts
            texts = [c["text"] for c in chunks]
            embeddings = embed_texts(texts, batch_size=32)

            # Store in DB
            db_chunks = []
            for chunk, embedding in zip(chunks, embeddings):
                try:
                    chunk_id_val = uuid.UUID(chunk["chunk_id"]) if isinstance(chunk["chunk_id"], str) else chunk["chunk_id"]
                except ValueError:
                    chunk_id_val = uuid.uuid4()
                db_chunks.append(DocumentChunk(
                    chunk_id=chunk_id_val,
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
                ))
            db.bulk_save_objects(db_chunks)

        material.status = "ingested"
        material.chunk_count = len(chunks)
        material.error_message = None
    except Exception as e:
        logger.exception("Ingestion failed for course material %s", material.id)
        material.status = "error"
        material.error_message = str(e)
    finally:
        db.commit()
