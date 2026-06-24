"""Full RAG pipeline — the main entry point for generation.

Today (Day 2) the pipeline simply formats chunks and calls the LLM via
``RAGGenerator``. The grader and citation stages are wired in on later days; the
``run`` method documents exactly where each one will slot in.
"""

from ai.rag.generator import RAGGenerator


class RAGPipeline:
    """Full RAG pipeline: question + chunks -> LLM -> structured response.

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
        chunks: list,
        student_profile: dict = None,
    ) -> dict:
        """Run the pipeline for a single question.

        Today (Day 2): passes chunks directly to the generator.
        """
        # TODO Day 5: retrieval grader — filter irrelevant chunks before generation.

        # Step: generate the answer.
        result = self.generator.generate(
            question, chunks, student_profile=student_profile
        )

        # TODO Day 4: citation formatting — parse [Source, p.X] into structured citations.
        # TODO Day 6: groundedness grader — validate the answer against the chunks.

        return result
