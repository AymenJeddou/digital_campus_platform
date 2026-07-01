"""Day 4 — Embedding generation.

Model: sentence-transformers/paraphrase-multilingual-mpnet-base-v2
Dimension: 768
Supports Arabic, French, English — all FSB document languages.

Loaded once and cached for the process lifetime via ``@lru_cache``.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
EMBEDDING_DIM = 768


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    logger.info("Loading embedding model: %s", MODEL_NAME)
    model = SentenceTransformer(MODEL_NAME)
    logger.info("Embedding model ready (dim=%d)", EMBEDDING_DIM)
    return model


def embed_texts(texts: list[str], batch_size: int = 32, show_progress: bool = False) -> list[list[float]]:
    """Embed a list of texts. Returns one 768-d vector per text."""
    if not texts:
        return []
    model = _get_model()
    vectors = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=show_progress,
        convert_to_numpy=True,
        normalize_embeddings=True,  # cosine sim = dot product on unit vectors
    )
    return vectors.tolist()


def embed_query(query: str) -> list[float]:
    """Embed a single query string (runtime path)."""
    return embed_texts([query])[0]
