"""Semantic search layer — FSBridge V2 (Iheb Bouali).

This is the stable seam the RAG pipeline calls (``RAGPipeline._retrieve`` →
``from src.search.retriever import retrieve``). The interface and return schema
are fixed; the body delegates to the pgvector implementation in ``ai.rag.search``.

Return schema (every dict): chunk_id, text, title, source, page, category, score
- score:   cosine similarity in [0, 1] (embeddings are L2-normalized).
- page:    section/page index within the document.
- category: opaque string set at ingestion from the folder.

Heavy imports (embeddings/torch, the DB engine) are deferred to call time, so
importing this module stays cheap and dependency-free.
"""


def retrieve(
    query: str,
    top_k: int = 5,
    category_filter: "list[str] | None" = None,
) -> "list[dict]":
    """Return the top-K relevant chunks for ``query`` via pgvector search.

    Args:
        query: The student's question (Arabic / French / English).
        top_k: Maximum number of chunks to return.
        category_filter: Optional categories to restrict the search to. The
            underlying search filters by a single category, so when exactly one
            is given it is applied; otherwise the search runs across all
            categories and relevance ranking decides.

    Returns:
        A list of chunk dicts following the FSBridge V2 schema.
    """
    # Deferred imports: keep module import cheap and free of torch/DB deps.
    from ai.rag.db import get_session
    from ai.rag.search import semantic_search

    category = None
    if category_filter and len(category_filter) == 1:
        category = category_filter[0]

    db = get_session()
    try:
        return semantic_search(db, query, top_k=top_k, category=category)
    finally:
        db.close()
