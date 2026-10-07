"""The FSB Nexus agent.

The four agents (orientation, academic, administrative, learning) differ only
by the scope rule in their prompt, so one class covers them all. The LLM call
goes through the provider-agnostic client (``ai.llm.client``).
"""

import os

from ai.llm.client import get_llm
from ai.prompts.system_prompts import get_prompt


def _generation_temperature() -> float | None:
    """Generation temperature from GENERATION_TEMPERATURE, else the client default."""
    raw = os.getenv("GENERATION_TEMPERATURE")
    return float(raw) if raw not in (None, "") else None


class BaseAgent:
    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        # Raises ValueError if the provider's API key is missing/placeholder.
        self._llm = get_llm()

    @staticmethod
    def _format_chunks(chunks: list) -> str:
        """Render retrieved chunks ``{chunk_id, text, title, source, page, ...}``
        into the context block, labelled the way the answer must cite them."""
        if not chunks:
            return "Aucun contexte disponible."
        return "\n\n---\n\n".join(
            f"[{chunk.get('title') or chunk.get('source', 'Source inconnue')}, p.{chunk.get('page', '?')}]\n"
            f"{chunk.get('text', '')}"
            for chunk in chunks
        )

    def _prompt(self, question, chunks, student_profile, history):
        profile = student_profile or {}
        return get_prompt(
            agent_type=self.agent_type,
            student_status=profile.get("student_status", "prospective"),
            student_academic_year=profile.get("academic_year"),
            student_program=profile.get("program"),
            context=self._format_chunks(chunks),
            question=question,
            history=history,
        )

    def run(self, question: str, chunks: list, student_profile: dict = None, history: str = None) -> dict:
        """Returns ``{"answer", "agent", "chunks_used", "raw_response"}``."""
        prompt = self._prompt(question, chunks, student_profile, history)
        answer = self._llm.generate(prompt["user"], temperature=_generation_temperature(), system=prompt["system"])
        return {"answer": answer, "agent": self.agent_type, "chunks_used": len(chunks), "raw_response": answer}

    def run_stream(self, question: str, chunks: list, student_profile: dict = None, history: str = None):
        prompt = self._prompt(question, chunks, student_profile, history)
        return self._llm.generate_stream(prompt["user"], temperature=_generation_temperature(), system=prompt["system"])
