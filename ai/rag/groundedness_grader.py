"""Groundedness grader (Day 6).

After generation, verify that every claim in the answer is actually supported by
the retrieved chunks. If not, the pipeline blocks the answer and returns the safe
refusal sentence — the last line of defence against hallucination, targeting the
RAG Triad "groundedness = 100%" goal.

This grader uses an LLM judge. By default it uses the active provider's
generation model; set ``GROUNDEDNESS_GRADER_MODEL`` to use a cheaper, independent
judge (e.g. ``mistral-small-latest``) — judging with a different model avoids the
self-grading bias of a model rating its own output.

Fail-safe: only an explicit "OUI" verdict counts as grounded; anything else
(including "NON" or an unparseable reply) is treated as NOT grounded.
"""

import logging
import os

from ai.agents.base_agent import BaseAgent
from ai.llm.client import get_llm

logger = logging.getLogger(__name__)

_GROUNDEDNESS_PROMPT = """Tu es un vérificateur de fiabilité (groundedness).
On te donne un CONTEXTE (extraits de documents FSB) et une RÉPONSE.
Vérifie si CHAQUE affirmation de la RÉPONSE est directement appuyée par le CONTEXTE.
Réponds par un seul mot, sans aucune explication :
- "OUI" si toute la réponse est appuyée par le contexte.
- "NON" si au moins une affirmation n'est pas appuyée par le contexte.

CONTEXTE:
{context}

RÉPONSE:
{answer}

Verdict (OUI ou NON):"""


def grade_groundedness(answer: str, chunks: list, llm=None) -> bool:
    """Return True if ``answer`` is fully supported by ``chunks``.

    Args:
        answer: The generated answer to verify.
        chunks: The chunks the answer was generated from.
        llm: Optional LLM client (injected for tests); otherwise built from the
            configured provider and ``GROUNDEDNESS_GRADER_MODEL``.
    """
    if not chunks or not answer:
        return False

    context = BaseAgent._format_chunks(chunks)
    prompt = _GROUNDEDNESS_PROMPT.format(context=context, answer=answer)

    llm = llm or get_llm(model=os.getenv("GROUNDEDNESS_GRADER_MODEL"))
    verdict = (llm.generate(prompt) or "").strip().lstrip("\"'").upper()
    return verdict.startswith("OUI")
