"""RAG generation entry point.

``RAGGenerator`` validates the requested agent type, instantiates the matching
agent, and delegates generation to it. This is the single object the backend
``/chat`` endpoint will call once the pipeline is wired (Issue #5, Day 6).
"""

from ai.agents.academic_agent import AcademicAgent
from ai.agents.administrative_agent import AdministrativeAgent
from ai.agents.learning_agent import LearningAgent
from ai.agents.orientation_agent import OrientationAgent
from ai.prompts.system_prompts import AGENT_TYPES

# Fake chunks used for local testing before the retriever is connected (Day 2).
# Shape matches the Knowledge Base handoff format (Issue #3).
FAKE_CHUNKS = [
    {
        "chunk_id": "test_001",
        "text": "Les étudiants de L2 doivent s'inscrire avant le 15 octobre.",
        "source": "Guide Académique FSB",
        "page": 12,
        "category": "course",
        "score": 0.95,
    },
    {
        "chunk_id": "test_002",
        "text": "La faculté propose trois licences: Informatique, Mathématiques et Physique.",
        "source": "Guide d'Orientation FSB",
        "page": 3,
        "category": "orientation",
        "score": 0.88,
    },
]

# Maps an agent type to its concrete class.
_AGENT_CLASSES = {
    "orientation": OrientationAgent,
    "academic": AcademicAgent,
    "administrative": AdministrativeAgent,
    "learning": LearningAgent,
}


class RAGGenerator:
    """Routes a question to the correct agent and returns its answer."""

    def __init__(self, agent_type: str):
        if agent_type not in _AGENT_CLASSES:
            raise ValueError(
                f"Unknown agent_type '{agent_type}'. Expected one of {AGENT_TYPES}."
            )
        self.agent_type = agent_type
        self.agent = _AGENT_CLASSES[agent_type]()

    def generate(
        self,
        question: str,
        chunks: list,
        student_status: str = "prospective",
        student_academic_year: str = None,
        student_profile: dict = None,
    ) -> dict:
        """Generate an answer for ``question`` from the given ``chunks``.

        If ``student_profile`` is provided it overrides ``student_status`` and
        ``student_academic_year`` (convenient single-dict contract for the
        backend ``/chat`` endpoint).
        """
        if student_profile:
            student_status = student_profile.get("student_status", "prospective")
            student_academic_year = student_profile.get("academic_year", None)

        try:
            return self.agent.run(
                question=question,
                chunks=chunks,
                student_status=student_status,
                student_academic_year=student_academic_year,
            )
        except ValueError:
            # Configuration errors (e.g. missing API key) must surface clearly.
            raise
        except Exception as e:  # noqa: BLE001 — return a safe, structured error
            return {
                "answer": "Une erreur est survenue lors de la génération de la réponse.",
                "agent": self.agent_type,
                "chunks_used": 0,
                "error": str(e),
            }
