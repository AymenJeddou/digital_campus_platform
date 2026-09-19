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
La RÉPONSE est fiable si son INFORMATION PRINCIPALE est appuyée par le CONTEXTE.
Une reformulation, un résumé, ou une phrase de politesse ne rendent PAS la réponse
non fiable. Elle n'est non fiable que si elle affirme un FAIT (chiffre, nom, date,
procédure) qui CONTREDIT le contexte ou qui en est totalement absent.
Réponds par un seul mot, sans explication :
- "OUI" si l'information principale de la réponse est appuyée par le contexte.
- "NON" si la réponse invente ou contredit un fait absent du contexte.

CONTEXTE:
{context}

RÉPONSE:
{answer}

Verdict (OUI ou NON):"""


def _verdict(text: str) -> str:
    """Parse a judge reply into 'OUI' / 'NON' / '' (unparseable)."""
    t = (text or "").strip().lstrip("\"'").upper()
    if t.startswith("OUI"):
        return "OUI"
    if t.startswith("NON"):
        return "NON"
    # Model ignored the "one word" instruction — look inside the reply.
    if "OUI" in t and "NON" not in t:
        return "OUI"
    if "NON" in t and "OUI" not in t:
        return "NON"
    return ""


def grade_groundedness(answer: str, chunks: list, llm=None) -> bool:
    """Return True if ``answer``'s main information is supported by ``chunks``.

    Robust to Mistral's residual non-determinism (temp 0 reduces but does not
    guarantee it): an unparseable or empty first verdict triggers ONE retry
    before defaulting to a block, so a stray reply doesn't refuse a valid answer.

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
    # Judge at a low temperature (default 0): a verdict should not be a dice roll.
    temp = float(os.getenv("GROUNDEDNESS_TEMPERATURE", "0"))

    v = _verdict(llm.generate(prompt, temperature=temp))
    if v == "":
        # Unparseable first reply — retry once rather than refuse on noise.
        v = _verdict(llm.generate(prompt, temperature=temp))
        logger.info("Groundedness verdict needed a retry (first reply unparseable).")
    return v == "OUI"
