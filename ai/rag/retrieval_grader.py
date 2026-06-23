"""Retrieval grader (Day 5).

Filters out irrelevant chunks before they reach the LLM. Implemented on Day 5;
this stub documents the intended contract.
"""


def grade_retrieval(question: str, chunk: dict) -> bool:
    """Return True if ``chunk`` is relevant to ``question``.

    To be implemented on Day 5. Until then, treat all chunks as relevant so the
    pipeline remains runnable.
    """
    raise NotImplementedError("grade_retrieval will be implemented on Day 5.")
