"""Day 5 — Vector store integration.

Connects to the existing ``document_chunks`` table in PostgreSQL + pgvector.
Compatible with the SQLAlchemy models in ``backend/app/models/models.py``.

Chunk dict format (matches ``FAKE_CHUNKS`` in generator.py and the KB handoff):
    {chunk_id, text, source, page, category, score}
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy.orm import Session

from ai.rag.embeddings import embed_texts

logger = logging.getLogger(__name__)


def store_chunks(
    db: Session,
    chunks: list[dict[str, Any]],
    document_id: uuid.UUID,
    batch_size: int = 32,
) -> int:
    """Embed chunks and persist them to ``document_chunks``.

    Args:
        db: Active SQLAlchemy session (from ``backend/app/db/database.py``).
        chunks: List of chunk dicts (text, source, page, category, chunk_id).
        document_id: FK to the parent ``documents`` row.
        batch_size: Embedding batch size.

    Returns:
        Number of chunks stored.
    """
    # Import here to avoid hard dependency when running ai/ standalone
    from backend.app.models.models import DocumentChunk  # noqa: PLC0415

    if not chunks:
        return 0

    texts = [c["text"] for c in chunks]
    embeddings = embed_texts(texts, batch_size=batch_size, show_progress=True)

    objects = []
    for chunk, embedding in zip(chunks, embeddings):
        objects.append(DocumentChunk(
            chunk_id=uuid.UUID(chunk["chunk_id"]) if "chunk_id" in chunk else uuid.uuid4(),
            document_id=document_id,
            text=chunk["text"],
            title=chunk.get("source", ""),
            source=chunk.get("source", ""),
            page=chunk.get("page", 0),
            category=chunk.get("category", "general"),
            embedding=embedding,
        ))

    db.bulk_save_objects(objects)
    db.commit()
    logger.info("Stored %d chunks for document_id=%s", len(objects), document_id)
    return len(objects)
