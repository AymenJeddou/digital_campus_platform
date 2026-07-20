"""Base class shared by the 4 FSB Nexus agents.

The LLM call is delegated to a provider-agnostic client (``ai.llm.client``), so
the agents work with either Gemini or Mistral depending on ``LLM_PROVIDER`` — no
code change to switch.

Citation parsing / formatting is layered on by the pipeline (Day 4); ``run``
returns the raw answer plus light metadata.
"""

from ai.llm.client import get_llm
from ai.prompts.system_prompts import get_prompt


class BaseAgent:
    """Common LLM-backed agent. Subclasses set ``agent_type``."""

    #: Overridden by each concrete agent (one of ``AGENT_TYPES``).
    agent_type: str = ""

    def __init__(self):
        # Builds the client for the configured provider; raises ValueError if the
        # provider's API key is missing/placeholder.
        self._llm = get_llm()

    @staticmethod
    def _format_chunks(chunks: list) -> str:
        """Render retrieved chunks into a readable context block for the prompt.

        Each chunk follows the FSBridge V2 schema (Iheb's handoff):
        ``{chunk_id, text, title, source, page, category, score}``.
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
            ``{"answer", "agent", "chunks_used", "raw_response"}``.
        """
        context = self._format_chunks(chunks)
        prompt = get_prompt(
            agent_type=self.agent_type,
            student_status=student_status,
            student_academic_year=student_academic_year,
            context=context,
            question=question,
        )

        answer = self._llm.generate(prompt)

        return {
            "answer": answer,
            "agent": self.agent_type,
            "chunks_used": len(chunks),
            "raw_response": answer,
        }

    def run_stream(
        self,
        question: str,
        chunks: list,
        student_status: str,
        student_academic_year: str,
    ):
        context = self._format_chunks(chunks)
        prompt = get_prompt(
            agent_type=self.agent_type,
            student_status=student_status,
            student_academic_year=student_academic_year,
            context=context,
            question=question,
        )
        return self._llm.generate_stream(prompt)
