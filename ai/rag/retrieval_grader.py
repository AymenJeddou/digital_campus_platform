"""Retrieval grader (Day 5).

Filters out irrelevant chunks before they reach the LLM.
Uses a lightweight Gemini call with a strict yes/no prompt so cost stays low.
Falls back to ``True`` (keep the chunk) on any API error, to avoid silently
dropping good results.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
_PLACEHOLDER_KEY = "your_gemini_api_key_here"

_GRADER_PROMPT = """\
Tu es un évaluateur de pertinence strict.

Question: {question}

Extrait de document:
{chunk_text}

Réponds UNIQUEMENT par "oui" si l'extrait contient des informations utiles pour répondre à la question, ou "non" sinon.
"""


def _get_model():
    load_dotenv(_ENV_PATH)
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == _PLACEHOLDER_KEY:
        raise ValueError("GEMINI_API_KEY is not configured.")
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(model_name)


def grade_retrieval(question: str, chunk: dict) -> bool:
    """Return True if ``chunk`` is relevant to ``question``.

    Args:
        question: The student's question.
        chunk: A chunk dict with at least a ``text`` key.

    Returns:
        True if the chunk should be kept, False if it should be filtered out.
    """
    try:
        model = _get_model()
        prompt = _GRADER_PROMPT.format(
            question=question,
            chunk_text=chunk.get("text", ""),
        )
        response = model.generate_content(prompt)
        answer = response.text.strip().lower()
        return answer.startswith("oui")
    except Exception as exc:
        # On any error (API down, quota, etc.) keep the chunk — fail open.
        logger.warning("grade_retrieval failed (%s) — keeping chunk by default", exc)
        return True


def filter_chunks(question: str, chunks: list[dict]) -> list[dict]:
    """Grade all chunks and return only the relevant ones.

    Args:
        question: The student's question.
        chunks: List of retrieved chunk dicts.

    Returns:
        Filtered list containing only relevant chunks.
        Falls back to the original list if all chunks are graded out,
        to ensure the pipeline always has something to work with.
    """
    graded = [chunk for chunk in chunks if grade_retrieval(question, chunk)]
    if not graded:
        logger.warning("All chunks filtered out by retrieval grader — using original set")
        return chunks
    return graded
