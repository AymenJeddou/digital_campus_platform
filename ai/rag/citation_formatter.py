"""Citation formatter (Day 4).

Parses inline citation markers ([Nom du document, p.X]) from the LLM output and
returns a structured response with a ``citations`` list.

If the LLM produces no citation marker at all, the top retrieved chunk is
appended automatically as a fallback citation.
"""

from __future__ import annotations

import re
from typing import Any

# Matches: [Nom du document, p.12]  or  [Nom du document, p.?]
_CITATION_RE = re.compile(r"\[([^\],]+),\s*p\.(\d+|\?)\]")


def format_citations(answer: str, chunks: list) -> dict[str, Any]:
    """Return ``{"answer": str, "citations": [{"document": str, "page": int|None}]}``.

    Args:
        answer: Raw LLM output, may contain inline markers like [Guide FSB, p.3].
        chunks: Retrieved chunks (dicts with at least ``source`` and ``page``).

    Returns:
        Dict with the original answer and a deduplicated list of citations.
    """
    found: list[dict[str, Any]] = []
    seen: set[tuple[str, Any]] = set()

    for match in _CITATION_RE.finditer(answer):
        doc = match.group(1).strip()
        raw_page = match.group(2)
        page: int | None = int(raw_page) if raw_page.isdigit() else None
        key = (doc, page)
        if key not in seen:
            seen.add(key)
            found.append({"document": doc, "page": page})

    # Fallback: if the LLM cited nothing, use the top chunk automatically.
    if not found and chunks:
        top = chunks[0]
        found.append({
            "document": top.get("source", "Source inconnue"),
            "page": top.get("page"),
        })

    return {"answer": answer, "citations": found}
