"""Citation formatter (Day 4).

Parses the inline citation markers the agents emit ([Nom du document, p.X]) out
of the answer text and returns a structured ``citations`` list. Keeps the inline
markers in ``answer`` (the frontend can render them as chips); adds the parsed
list on top.

Fallback: if a real answer carries no citation, the top retrieved chunk's source
is attached automatically, so an answer is never left uncited.
"""

import re

from ai.prompts.system_prompts import NO_INFO_SENTENCE

# Matches "[Nom du document, p.X]" — tolerant of "p.3", "p. 3", "p 3".
_CITATION_RE = re.compile(r"\[([^\[\]]+?),\s*p\.?\s*(\d+)\]")


def _is_refusal(answer: str) -> bool:
    """True when the answer is (or contains only) the fixed refusal sentence."""
    return NO_INFO_SENTENCE.strip(' "') in (answer or "")


def format_citations(answer: str, chunks: list) -> dict:
    """Extract structured citations from an answer.

    Args:
        answer: The LLM answer text (may contain ``[document, p.X]`` markers).
        chunks: The chunks the answer was generated from (used for the fallback).

    Returns:
        ``{"answer": str, "citations": [{"document": str, "page": int}, ...]}``.
        Citations are de-duplicated and kept in order of first appearance.
    """
    answer = answer or ""
    citations = []
    seen = set()
    for doc, page in _CITATION_RE.findall(answer):
        key = (doc.strip(), int(page))
        if key not in seen:
            seen.add(key)
            citations.append({"document": doc.strip(), "page": int(page)})

    # Fallback: a real answer with no citation gets the top chunk attached.
    if not citations and chunks and not _is_refusal(answer):
        top = chunks[0]
        document = top.get("title") or top.get("source", "Source inconnue")
        page = top.get("page", 0)
        citations.append({"document": document, "page": page})

    return {"answer": answer, "citations": citations}
