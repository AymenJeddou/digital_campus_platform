"""Retrieval grader (Day 5).

Filters out irrelevant chunks before they reach the LLM, using the cosine
similarity ``score`` (in [0, 1]) that the FSBridge V2 retriever attaches to each
chunk. This is a free, deterministic relevance gate — no LLM call.

The threshold defaults to ``DEFAULT_THRESHOLD`` and can be overridden per
environment via ``RETRIEVAL_SCORE_THRESHOLD``. It is a starting value; calibrate
it on Day 7 against real score distributions from the retriever.
"""

import os

# Starting threshold — chunks scoring below this are dropped. Tune on Day 7.
DEFAULT_THRESHOLD = 0.5


def _threshold(threshold: float = None) -> float:
    if threshold is not None:
        return threshold
    try:
        return float(os.getenv("RETRIEVAL_SCORE_THRESHOLD", DEFAULT_THRESHOLD))
    except (TypeError, ValueError):
        return DEFAULT_THRESHOLD


def grade_retrieval(question: str, chunk: dict, threshold: float = None) -> bool:
    """Return True if ``chunk`` is relevant enough to keep.

    Args:
        question: The student's question. Accepted for the grader contract and a
            future LLM-based grader; not used by the score-threshold version.
        chunk: A chunk dict; relevance is read from ``chunk["score"]``.
        threshold: Optional explicit cutoff (else env / default).

    A chunk with no ``score`` is kept (we can't grade it, so we don't drop it —
    e.g. chunks passed directly by the backend).
    """
    score = chunk.get("score")
    if score is None:
        return True
    return score >= _threshold(threshold)


def filter_chunks(question: str, chunks: list, threshold: float = None) -> list:
    """Return only the chunks that pass ``grade_retrieval``."""
    return [c for c in chunks if grade_retrieval(question, c, threshold)]
