"""Full RAG pipeline — the main entry point for generation.

Day 6: All stages now wired in:
  - Day 5: Retrieval grader filters irrelevant chunks before the LLM.
  - Day 2: RAGGenerator calls the correct agent with the filtered chunks.
  - Day 4: Citation formatter parses [Source, p.X] markers into structured output.
  - Day 6: Groundedness grader validates the answer; falls back to NO_INFO_SENTENCE
           if hallucination is detected.
"""

from ai.prompts.system_prompts import NO_INFO_SENTENCE
from ai.rag.citation_formatter import format_citations
from ai.rag.generator import RAGGenerator
from ai.rag.groundedness_grader import grade_groundedness
from ai.rag.retrieval_grader import filter_chunks


class RAGPipeline:
    """Full RAG pipeline: question + chunks -> grader -> LLM -> citations -> grounded answer."""

    def __init__(self, agent_type: str):
        # RAGGenerator validates ``agent_type`` and raises ValueError if invalid.
        self.agent_type = agent_type
        self.generator = RAGGenerator(agent_type)

    def run(
        self,
        question: str,
        chunks: list,
        student_profile: dict = None,
    ) -> dict:
        """Run the full pipeline for a single question.

        Args:
            question: The student's question (Arabic / French / English).
            chunks: Retrieved chunks from the vector store (pgvector, Day 5).
            student_profile: Dict with ``student_status`` and ``academic_year``.

        Returns:
            ``{"answer": str, "agent": str, "chunks_used": int, "citations": list}``
        """
        # Day 5: Filter out irrelevant chunks before generation.
        relevant_chunks = filter_chunks(question, chunks)

        # Day 2: Generate the answer using the correct FSB agent.
        result = self.generator.generate(
            question, relevant_chunks, student_profile=student_profile
        )

        answer = result.get("answer", NO_INFO_SENTENCE)

        # Day 6: Groundedness check — block hallucinated answers.
        if not grade_groundedness(answer, relevant_chunks):
            answer = NO_INFO_SENTENCE

        # Day 4: Parse inline citations into structured list.
        formatted = format_citations(answer, relevant_chunks)

        return {
            "answer": formatted["answer"],
            "agent": result.get("agent", self.agent_type),
            "chunks_used": result.get("chunks_used", len(relevant_chunks)),
            "citations": formatted["citations"],
        }
