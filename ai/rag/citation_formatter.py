"""Citation formatter (Day 4).

Parses inline citation markers ([Nom du document, p.X]) from the LLM output and
returns a structured response with a ``citations`` list. Implemented on Day 4;
this stub documents the intended contract.
"""


def format_citations(answer: str, chunks: list) -> dict:
    """Return ``{"answer": str, "citations": [{"document", "page"}]}``.

    To be implemented on Day 4. Fallback behaviour: if the LLM produces no
    citation, append the top retrieved source automatically.
    """
    raise NotImplementedError("format_citations will be implemented on Day 4.")
