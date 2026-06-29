"""Groundedness grader (Day 6).

Verifies the generated answer is strictly supported by the retrieved context.
If an answer is not grounded, the caller should block it and return the safe
fallback sentence defined in ``system_prompts.NO_INFO_SENTENCE``.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv

from ai.prompts.system_prompts import NO_INFO_SENTENCE

logger = logging.getLogger(__name__)

_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
_PLACEHOLDER_KEY = "your_gemini_api_key_here"

_GRADER_PROMPT = """\
Tu es un vérificateur de véracité strict.

Contexte (seule source autorisée):
{context}

Réponse générée:
{answer}

La réponse est-elle ENTIÈREMENT basée sur le contexte fourni, sans aucune information inventée?
Réponds UNIQUEMENT par "oui" ou "non".
"""


def _get_model():
    load_dotenv(_ENV_PATH)
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == _PLACEHOLDER_KEY:
        raise ValueError("GEMINI_API_KEY is not configured.")
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(model_name)


def _chunks_to_context(chunks: list[dict]) -> str:
    parts = [
        f"[{c.get('source', '?')}, p.{c.get('page', '?')}]\n{c.get('text', '')}"
        for c in chunks
    ]
    return "\n\n---\n\n".join(parts) if parts else "Aucun contexte."


def grade_groundedness(answer: str, chunks: list) -> bool:
    """Return True if ``answer`` is grounded in ``chunks``.

    Args:
        answer: The LLM-generated answer string.
        chunks: The retrieved chunk dicts used to generate the answer.

    Returns:
        True if grounded, False if hallucination detected.
        Falls back to True on API errors to avoid blocking valid answers.
    """
    # The standard refusal sentence is always considered grounded.
    if NO_INFO_SENTENCE in answer:
        return True

    try:
        model = _get_model()
        context = _chunks_to_context(chunks)
        prompt = _GRADER_PROMPT.format(context=context, answer=answer)
        response = model.generate_content(prompt)
        result = response.text.strip().lower()
        return result.startswith("oui")
    except Exception as exc:
        logger.warning("grade_groundedness failed (%s) — treating as grounded", exc)
        return True
