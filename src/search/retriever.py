"""Semantic search layer — FSBridge V2 (Iheb Bouali → Aymen).

DAY 3 MOCK. This is the agreed interface contract from Iheb's handoff. The real
implementation (pgvector + paraphrase-multilingual-mpnet-base-v2 embeddings)
lands end of Day 6; the function *signature and return schema below are final* —
only the body gets swapped, so the RAG pipeline needs no changes.

Return schema (every dict): chunk_id, text, title, source, page, category, score
- score: cosine similarity in [0.0, 1.0] (L2-normalized; safe to threshold).
- page:  0-based section index within the document (NOT a printed page number).
- category: opaque string set at ingestion from the folder; do NOT hardcode its
  values on the consumer side — the taxonomy will change with the new schema.
"""


def retrieve(
    query: str,
    top_k: int = 5,
    category_filter: "list[str] | None" = None,
) -> "list[dict]":
    """Return the top-K relevant chunks for ``query``.

    Args:
        query: The student's question (raw text).
        top_k: Maximum number of chunks to return.
        category_filter: Optional list of categories to restrict the search to
            (translated to ``WHERE category = ANY(...)`` before vector search).
            ``None`` searches across all categories.

    Returns:
        A list of chunk dicts following the FSBridge V2 schema.
    """
    # --- MOCK BODY (Day 3). Real pgvector search swapped in on Day 6. ---
    return [
        {
            "chunk_id": "mock001",
            "text": f"[MOCK] Result for: {query}",
            "title": "FSB Guide 2025",
            "source": "guide2025_cleaned.md",
            "page": 1,
            "category": "orientation",
            "score": 0.91,
        }
    ]
