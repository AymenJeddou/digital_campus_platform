"""Full RAG pipeline: question -> retrieve -> grade -> LLM -> cite -> verify."""

import logging
import os

from ai.agents.base_agent import BaseAgent
from ai.prompts.system_prompts import AGENT_TYPES, NO_INFO_SENTENCE
from ai.rag.citation_formatter import format_citations
from ai.rag.groundedness_grader import grade_groundedness
from ai.rag.retrieval_grader import filter_chunks

logger = logging.getLogger(__name__)


def _groundedness_enabled() -> bool:
    """Whether the post-generation groundedness judge runs (GROUNDEDNESS_ENABLED)."""
    return os.getenv("GROUNDEDNESS_ENABLED", "1") != "0"


class RAGPipeline:
    def __init__(self, agent_type: str):
        if agent_type not in AGENT_TYPES:
            raise ValueError(f"Unknown agent_type '{agent_type}'. Expected one of {AGENT_TYPES}.")
        self.agent_type = agent_type
        self.agent = BaseAgent(agent_type)

    def _refusal(self, chunks_used: int = 0) -> dict:
        return {"answer": NO_INFO_SENTENCE, "agent": self.agent_type, "chunks_used": chunks_used, "citations": []}

    def run(
        self,
        question: str,
        student_profile: dict = None,
        chunks: list = None,
        top_k: int = 5,
        category_filter: list = None,
        history: str = None,
        retrieval_query: str = None,
        stream: bool = False,
        student_id: str = None,
        course_id: str = None,
    ):
        """Answer one question.

        Args:
            question: The student's question.
            student_profile: ``{"student_status", "academic_year", "program"}``.
            chunks: If provided, used directly and retrieval is skipped.
            top_k / category_filter: passed to the retriever.
            history: Formatted recent turns, given to the generator only;
                retrieval and grounding use the current question alone.
            retrieval_query: Query used for retrieval instead of ``question``
                (e.g. a short follow-up augmented with the previous turn).
            stream: If True, returns ``(token_generator, chunks)``. The
                generator yields the answer then a final
                "[groundedness_check: <bool>]" marker. A streamed answer can't
                be retracted mid-way, so the caller flags it instead.
            student_id / course_id: include that student's course materials.

        Returns:
            ``{"answer", "agent", "chunks_used", "citations"}`` (non-streaming).
        """
        if chunks is None:
            chunks = self._retrieve(
                retrieval_query or question, top_k, category_filter,
                student_id=student_id, course_id=course_id,
            )

        # Drop weak chunks; with none left, refuse without calling the LLM.
        chunks = filter_chunks(question, chunks)
        if not chunks:
            return (iter([NO_INFO_SENTENCE]), []) if stream else self._refusal()

        if stream:
            def _stream_and_grade():
                answer = ""
                for token in self.agent.run_stream(question, chunks, student_profile, history):
                    answer += token
                    yield token
                if _groundedness_enabled() and answer.strip() != NO_INFO_SENTENCE:
                    yield f"\n\n[groundedness_check: {grade_groundedness(answer, chunks)}]"

            return _stream_and_grade(), chunks

        result = self.agent.run(question, chunks, student_profile, history)
        answer = result["answer"]
        result["citations"] = format_citations(answer, chunks)["citations"]

        # Block answers the judge finds unsupported by the retrieved chunks.
        if _groundedness_enabled() and answer and answer != NO_INFO_SENTENCE:
            if not grade_groundedness(answer, chunks):
                logger.warning(
                    "Groundedness grader BLOCKED an answer (agent=%s) | q=%r | answer=%r",
                    self.agent_type, question[:80], answer[:120],
                )
                return self._refusal(len(chunks))
        return result

    @staticmethod
    def _retrieve(question: str, top_k: int, category_filter: list,
                  student_id: str = None, course_id: str = None) -> list:
        """Fetch chunks from the semantic search layer (``src.search.retriever``),
        imported lazily so prompt-only code doesn't need the DB / torch."""
        from src.search.retriever import retrieve

        return retrieve(
            question, top_k=top_k, category_filter=category_filter,
            student_id=student_id, course_id=course_id,
        )
