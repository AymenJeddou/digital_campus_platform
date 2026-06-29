"""Day 6 — Semantic search via pgvector.

Embeds the query and retrieves the top-K most similar chunks using
pgvector's ``<=>`` cosine distance operator and an HNSW index.

The returned chunk format matches ``FAKE_CHUNKS`` in ``generator.py``:
    {chunk_id, text, source, page, category, score}
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from ai.rag.embeddings import embed_query

logger = logging.getLogger(__name__)

DEFAULT_TOP_K = 5
MIN_SIMILARITY = 0.25


def semantic_search(
    db: Session,
    question: str,
    top_k: int = DEFAULT_TOP_K,
    category: str | None = None,
    min_similarity: float = MIN_SIMILARITY,
) -> list[dict[str, Any]]:
    """Return the top-K most relevant chunks for ``question``.

    Args:
        db: Active SQLAlchemy session (PostgreSQL + pgvector required).
        question: Student question (any supported language).
        top_k: Maximum number of chunks to return.
        category: Optional filter on ``document_chunks.category``.
        min_similarity: Minimum cosine similarity threshold (0–1).

    Returns:
        List of chunk dicts compatible with ``RAGGenerator.generate()``:
        ``{chunk_id, text, source, page, category, score}``
    """
    query_vec = embed_query(question)
    max_distance = 1.0 - min_similarity

    category_clause = "AND dc.category = :category" if category else ""

    sql = text(f"""
        SELECT
            dc.chunk_id,
            dc.text,
            dc.source,
            dc.page,
            dc.category,
            1 - (dc.embedding <=> CAST(:query_vec AS vector)) AS similarity
        FROM document_chunks dc
        WHERE dc.embedding IS NOT NULL
          AND (dc.embedding <=> CAST(:query_vec AS vector)) <= :max_distance
          {category_clause}
        ORDER BY dc.embedding <=> CAST(:query_vec AS vector)
        LIMIT :top_k
    """)

    params: dict[str, Any] = {
        "query_vec": str(query_vec),
        "max_distance": max_distance,
        "top_k": top_k,
    }
    if category:
        params["category"] = category

    rows = db.execute(sql, params).fetchall()

    results = [
        {
            "chunk_id": str(row.chunk_id),
            "text": row.text,
            "source": row.source or "",
            "page": row.page or 0,
            "category": row.category or "general",
            "score": round(float(row.similarity), 4),
        }
        for row in rows
    ]

    logger.info(
        "semantic_search: '%s' → %d chunks (top_k=%d, min_sim=%.2f)",
        question[:60], len(results), top_k, min_similarity,
    )
    return results
