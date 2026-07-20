"""Semantic search via pgvector.

Embeds the query and retrieves the top-K most similar chunks using
pgvector's ``<=>`` cosine distance operator.

The corpus is small (~3.7k chunks), so recall — not speed — is what matters.
The ingest builds an ``ivfflat`` index, and ivfflat defaults to ``probes = 1``:
it scans a single cluster and can silently miss the true nearest neighbours,
which measurably dropped hit@5 from 0.80 (exact) to 0.50. We therefore raise
``ivfflat.probes`` to scan every cluster, recovering exact-search recall at a
cost that is negligible at this corpus size. (If the index is later removed,
this SET is a harmless no-op as long as the ``vector`` extension is installed.)

The returned chunk format matches ``FAKE_CHUNKS`` in ``generator.py``:
    {chunk_id, text, source, page, category, score}
"""

from __future__ import annotations

import logging
import os
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from ai.rag.embeddings import embed_query

logger = logging.getLogger(__name__)

DEFAULT_TOP_K = 5
MIN_SIMILARITY = 0.25
# Scan all ivfflat clusters (index is built with lists=100). Full recall at this
# corpus size; override via env if the index is ever rebuilt with more lists.
IVFFLAT_PROBES = int(os.getenv("IVFFLAT_PROBES", "100"))

# Hybrid retrieval: fuse vector + Postgres full-text via Reciprocal Rank Fusion.
HYBRID_SEARCH = os.getenv("HYBRID_SEARCH", "1") != "0"
CANDIDATE_POOL = int(os.getenv("RETRIEVAL_CANDIDATE_POOL", "40"))  # per arm
# Small RRF constant: on a tiny corpus the standard 60 flattens rank-1 advantage
# so a strong keyword winner never surfaces in the fused top-k. 15 keeps it sharp.
RRF_K = int(os.getenv("RRF_K", "15"))
KEYWORD_MATCH_FLOOR = 0.4  # keep keyword hits above the 0.35 relevance-grader cut


def _ensure_full_recall(db: Session) -> None:
    """Raise ivfflat.probes so the vector search scans every cluster, not just one."""
    try:
        db.execute(text("SET ivfflat.probes = :p"), {"p": IVFFLAT_PROBES})
    except Exception:  # extension/GUC absent (e.g. no ivfflat index) — exact search already
        db.rollback()


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
    _ensure_full_recall(db)
    query_vec = embed_query(question)
    cat_clause = "AND dc.category = :category" if category else ""
    cat_params = {"category": category} if category else {}

    # --- Vector arm: candidate pool of the closest chunks by cosine distance. ---
    vec_rows = db.execute(text(f"""
        SELECT dc.chunk_id, dc.text, dc.title, dc.source, dc.page, dc.category,
               1 - (dc.embedding <=> CAST(:qv AS vector)) AS similarity
        FROM document_chunks dc
        WHERE dc.embedding IS NOT NULL {cat_clause}
        ORDER BY dc.embedding <=> CAST(:qv AS vector)
        LIMIT :pool
    """), {"qv": str(query_vec), "pool": CANDIDATE_POOL, **cat_params}).fetchall()

    # --- Keyword arm: French full-text, for exact-term queries the vector arm
    #     fumbles (e.g. "retirer inscription", "coordinateurs"). Built-in Postgres
    #     FTS -- no new dependency, no schema change. ---
    kw_rows = []
    if HYBRID_SEARCH:
        # OR the query terms: plainto_tsquery ANDs every word, so an interrogative
        # ("Comment changer de parcours") would require the doc to contain "comment"
        # and match nothing. websearch_to_tsquery with " or " gives OR + stemming and
        # parses raw user text safely. Weight title (A) >> body (D) so a small on-topic
        # doc ("Formulaire de changement de parcours") beats big docs that mention the
        # terms in passing.
        kw_query = " or ".join(question.replace("?", " ").split()) or question
        kw_rows = db.execute(text(f"""
            SELECT dc.chunk_id, dc.text, dc.title, dc.source, dc.page, dc.category,
                   ts_rank('{{0.1,0.2,0.4,1.0}}',
                           setweight(to_tsvector('french', coalesce(dc.title,'')), 'A') ||
                           setweight(to_tsvector('french', dc.text), 'D'),
                           websearch_to_tsquery('french', :q)) AS rank
            FROM document_chunks dc
            WHERE (setweight(to_tsvector('french', coalesce(dc.title,'')), 'A') ||
                   setweight(to_tsvector('french', dc.text), 'D'))
                  @@ websearch_to_tsquery('french', :q) {cat_clause}
            ORDER BY rank DESC
            LIMIT :pool
        """), {"q": kw_query, "pool": CANDIDATE_POOL, **cat_params}).fetchall()

    # --- Reciprocal Rank Fusion of the two arms. ---
    fused: dict[str, dict[str, Any]] = {}
    for i, row in enumerate(vec_rows):
        cid = str(row.chunk_id)
        d = fused.setdefault(cid, {"row": row, "cos": round(float(row.similarity), 4),
                                   "kw": False, "rrf": 0.0})
        d["rrf"] += 1.0 / (RRF_K + i + 1)
    for i, row in enumerate(kw_rows):
        cid = str(row.chunk_id)
        d = fused.setdefault(cid, {"row": row, "cos": None, "kw": False, "rrf": 0.0})
        d["kw"] = True
        d["rrf"] += 1.0 / (RRF_K + i + 1)

    ranked = sorted(fused.values(), key=lambda d: d["rrf"], reverse=True)[:top_k]

    results = []
    for d in ranked:
        row = d["row"]
        cos = d["cos"] if d["cos"] is not None else 0.0
        # A strong keyword match is strong evidence: floor its score so the
        # downstream relevance grader (drops score < 0.35) cannot silently kill it.
        score = max(cos, KEYWORD_MATCH_FLOOR) if d["kw"] else cos
        # Vector-only chunks must still clear the caller's similarity floor.
        if not d["kw"] and cos < min_similarity:
            continue
        results.append({
            "chunk_id": str(row.chunk_id),
            "text": row.text,
            "title": row.title or row.source or "",
            "source": row.source or "",
            "page": row.page or 0,
            "category": row.category or "general",
            "score": round(score, 4),
        })

    logger.info(
        "semantic_search: '%s' → %d chunks (top_k=%d, hybrid=%s)",
        question[:60], len(results), top_k, HYBRID_SEARCH,
    )
    return results
