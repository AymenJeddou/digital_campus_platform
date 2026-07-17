"""Backend integration entrypoint for the RAG pipeline.

The backend's chat service dynamically imports a handler via the
``RAG_PIPELINE_HANDLER`` setting (``module:function``). Point it here:

    RAG_PIPELINE_HANDLER=ai.integration:answer_chat

This adapter turns the backend's call shape into a ``RAGPipeline`` call and
returns ``{"answer", "citations"}`` for the chat response.
"""

from ai.rag.pipeline import RAGPipeline

# Default agent when none is derived from the profile.
_DEFAULT_AGENT = "orientation"


def _route_agent(student) -> str:
    """Pick an agent from the student profile.

    Newcomers (prospective) default to Orientation; enrolled students default to
    Academic. Kept deliberately simple — routing can be refined later without
    touching the backend.
    """
    status = getattr(student, "student_status", None)
    if status == "enrolled":
        return "academic"
    return _DEFAULT_AGENT


def answer_chat(message: str, session_id=None, student=None) -> dict:
    """Generate a grounded, cited answer for a chat message.

    Args:
        message: The student's question.
        session_id: Chat session id (unused here; kept for the backend contract).
        student: The Student row; ``student_status`` / ``academic_year`` are
            injected as system context.

    Returns:
        ``{"answer": str, "citations": [{"document": str, "page": int}]}``
    """
    profile = {
        "student_status": getattr(student, "student_status", "prospective"),
        "academic_year": getattr(student, "academic_year", None),
    }
    agent_type = _route_agent(student)
    result = RAGPipeline(agent_type).run(message, student_profile=profile)
    return {"answer": result["answer"], "citations": result.get("citations", [])}

def answer_chat_stream(message: str, session_id=None, student=None):
    profile = {
        "student_status": getattr(student, "student_status", "prospective"),
        "academic_year": getattr(student, "academic_year", None),
    }
    agent_type = _route_agent(student)
    stream, chunks = RAGPipeline(agent_type).run(message, student_profile=profile, stream=True)
    return stream, chunks
