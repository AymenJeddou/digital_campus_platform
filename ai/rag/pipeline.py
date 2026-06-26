"""Full RAG pipeline — the main entry point for generation.

Day 3 connects the pipeline to Iheb's semantic search layer
(``src.search.retriever.retrieve``). ``run`` now retrieves chunks for a question
and feeds them to the generator. The backend may also pass ``chunks`` explicitly
to bypass retrieval (e.g. when it has already retrieved, or for tests).
"""

from ai.prompts.system_prompts import NO_INFO_SENTENCE
from ai.rag.citation_formatter import format_citations
from ai.rag.generator import RAGGenerator
from ai.rag.retrieval_grader import filter_chunks


class RAGPipeline:
    """Full RAG pipeline: question -> retrieve -> LLM -> structured response.

    Retrieval grader and groundedness grader will be added on Days 5 and 6.
    Citation formatting will be added on Day 4.
    """

    def __init__(self, agent_type: str):
        # RAGGenerator validates ``agent_type`` and raises ValueError if invalid.
        self.agent_type = agent_type
        self.generator = RAGGenerator(agent_type)

    def run(
        self,
        question: str,
        student_profile: dict = None,
        chunks: list = None,
        top_k: int = 5,
        category_filter: list = None,
    ) -> dict:
        """Run the pipeline for a single question.

        Args:
            question: The student's question.
            student_profile: ``{"student_status", "academic_year"}`` (injected).
            chunks: If provided, used directly and retrieval is skipped. Otherwise
                chunks are fetched via the semantic search layer.
            top_k: Number of chunks to retrieve (ignored when ``chunks`` given).
            category_filter: Optional list of categories to restrict retrieval to.
                Passed straight through to the retriever — the pipeline does NOT
                derive it from ``agent_type`` (per Iheb's handoff, category values
                are opaque and will change with the new schema).
        """
        if chunks is None:
            chunks = self._retrieve(question, top_k, category_filter)

        # Day 5: drop weak chunks before generation. If none survive, refuse
        # without calling the LLM.
        chunks = filter_chunks(question, chunks)
        if not chunks:
            return {
                "answer": NO_INFO_SENTENCE,
                "agent": self.agent_type,
                "chunks_used": 0,
                "citations": [],
            }

        result = self.generator.generate(
            question, chunks, student_profile=student_profile
        )

        # Day 4: parse [document, p.X] markers into a structured citations list.
        if "answer" in result and "error" not in result:
            formatted = format_citations(result["answer"], chunks)
            result["citations"] = formatted["citations"]

        # TODO Day 6: groundedness grader — validate the answer against the chunks.

        return result

    @staticmethod
    def _retrieve(question: str, top_k: int, category_filter: list) -> list:
        """Fetch chunks from the semantic search layer (Iheb's FSBridge V2).

        Imported lazily so the rest of the pipeline (and prompt-only tests) does
        not depend on the search module being importable.
        """
        try:
            from src.search.retriever import retrieve
        except ImportError as e:  # pragma: no cover - clear message if missing
            raise ImportError(
                "Semantic search layer not found (src/search/retriever.py). "
                "Pass `chunks=` explicitly, or ensure the retriever module is on "
                "the path."
            ) from e
        return retrieve(question, top_k=top_k, category_filter=category_filter)
