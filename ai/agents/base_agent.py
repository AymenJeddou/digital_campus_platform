"""Base class shared by the 4 FSB Nexus agents.

Handles Gemini client initialization (API key loaded from the environment via
``python-dotenv``) and the common ``run`` flow. Each concrete agent only needs
to declare its ``agent_type``.

Citation parsing / formatting is intentionally NOT done here — that is added on
Day 4 in ``rag/citation_formatter.py``. For now ``run`` returns the raw answer.
"""

import os

from dotenv import load_dotenv

from ai.prompts.system_prompts import get_prompt

# Model used for generation (per the work plan).
GENERATION_MODEL = "gemini-2.0-flash"

# Placeholder value shipped in .env.example — a real key must replace it.
_PLACEHOLDER_KEY = "your_gemini_api_key_here"


def _format_chunks(chunks: list) -> str:
    """Render retrieved chunks into a readable context block for the prompt.

    Each chunk is expected to follow the handoff format from the Knowledge Base
    role (Issue #3): ``{chunk_id, text, source, page, category, score}``.
    """
    if not chunks:
        return ""

    parts = []
    for chunk in chunks:
        source = chunk.get("source", "Document inconnu")
        page = chunk.get("page", "?")
        text = chunk.get("text", "")
        parts.append(f"[{source}, p.{page}]\n{text}")
    return "\n\n".join(parts)


class BaseAgent:
    """Common Gemini-backed agent. Subclasses set ``agent_type``."""

    #: Overridden by each concrete agent (one of ``AGENT_TYPES``).
    agent_type: str = ""

    def __init__(self):
        # Load variables from a local .env file if present.
        load_dotenv()
        self._api_key = os.getenv("GEMINI_API_KEY")
        # The Gemini client is created lazily in ``run`` so that importing an
        # agent (e.g. for prompt tests) never requires a configured key.
        self._model = None

    def _ensure_client(self):
        """Configure the Gemini client, validating the API key first."""
        if not self._api_key or self._api_key == _PLACEHOLDER_KEY:
            raise ValueError("GEMINI_API_KEY is not configured.")

        if self._model is None:
            # Imported here so prompt-only usage doesn't require the package.
            import google.generativeai as genai

            genai.configure(api_key=self._api_key)
            self._model = genai.GenerativeModel(GENERATION_MODEL)

    def run(
        self,
        question: str,
        chunks: list,
        student_status: str,
        student_academic_year: str,
    ) -> dict:
        """Generate an answer from the retrieved chunks.

        Returns:
            ``{"answer": str, "raw_response": str}``. Citation formatting will be
            layered on top of this on Day 4.

        Raises:
            ValueError: If the Gemini API key is not configured.
        """
        self._ensure_client()

        context = _format_chunks(chunks)
        prompt = get_prompt(
            agent_type=self.agent_type,
            student_status=student_status,
            student_academic_year=student_academic_year,
            context=context,
            question=question,
        )

        response = self._model.generate_content(prompt)
        answer = getattr(response, "text", "") or ""

        return {"answer": answer, "raw_response": str(response)}
