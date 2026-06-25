"""Base class shared by the 4 FSB Nexus agents.

Handles Gemini client initialization (API key loaded from the environment via
``python-dotenv``) and the common ``run`` flow. Each concrete agent only needs
to declare its ``agent_type``.

The Gemini client is validated and built eagerly in ``__init__`` so that a
misconfigured key fails fast and clearly, rather than at the first request.

Citation parsing / formatting is intentionally NOT done here — that is added on
Day 4 in ``rag/citation_formatter.py``. For now ``run`` returns the raw answer.
"""

import os
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv

from ai.prompts.system_prompts import get_prompt

# Default generation model. A current free-tier Flash model (gemini-2.0-flash
# was shut down 2026-06-01). Override per-environment with GEMINI_MODEL in .env.
DEFAULT_MODEL = "gemini-2.5-flash"

# Path to ai/.env so the key loads regardless of the current working directory.
_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"

# Placeholder value shipped in .env.example — a real key must replace it.
_PLACEHOLDER_KEY = "your_gemini_api_key_here"


class BaseAgent:
    """Common Gemini-backed agent. Subclasses set ``agent_type``."""

    #: Overridden by each concrete agent (one of ``AGENT_TYPES``).
    agent_type: str = ""

    def __init__(self):
        # Load variables from ai/.env if present (falls back to real env vars).
        load_dotenv(_ENV_PATH)
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key == _PLACEHOLDER_KEY:
            raise ValueError(
                "GEMINI_API_KEY is not configured. Copy .env.example to .env "
                "and add your real key."
            )

        model_name = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(model_name)

    @staticmethod
    def _format_chunks(chunks: list) -> str:
        """Render retrieved chunks into a readable context block for the prompt.

        Each chunk follows the Knowledge Base handoff format (Issue #3):
        ``{chunk_id, text, source, page, category, score}``.
        """
        if not chunks:
            return "Aucun contexte disponible."
        formatted = []
        for chunk in chunks:
            # Cite by the human-readable title when available (FSBridge V2 schema),
            # falling back to the source filename.
            label = chunk.get("title") or chunk.get("source", "Source inconnue")
            formatted.append(
                f"[{label}, p.{chunk.get('page', '?')}]\n{chunk.get('text', '')}"
            )
        return "\n\n---\n\n".join(formatted)

    def run(
        self,
        question: str,
        chunks: list,
        student_status: str,
        student_academic_year: str,
    ) -> dict:
        """Generate an answer from the retrieved chunks.

        Returns:
            ``{"answer", "agent", "chunks_used", "raw_response"}``. Citation
            formatting will be layered on top of this on Day 4.
        """
        context = self._format_chunks(chunks)
        prompt = get_prompt(
            agent_type=self.agent_type,
            student_status=student_status,
            student_academic_year=student_academic_year,
            context=context,
            question=question,
        )

        response = self._model.generate_content(prompt)

        return {
            "answer": response.text,
            "agent": self.agent_type,
            "chunks_used": len(chunks),
            "raw_response": response.text,
        }
