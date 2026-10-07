"""Backend integration entrypoint for the RAG pipeline.

The backend's chat service dynamically imports a handler via the
``RAG_PIPELINE_HANDLER`` setting (``module:function``). Point it here:

    RAG_PIPELINE_HANDLER=ai.integration:answer_chat

The backend passes the conversation history it already loaded (prior turns
only, oldest first), so this module never reads the chat tables itself.
"""

from ai.rag.intent import FACTUAL, classify_intent, conversational_reply, is_administrative
from ai.rag.pipeline import RAGPipeline

_DEFAULT_AGENT = "orientation"


def _format_history(history) -> tuple[str | None, str | None]:
    """``[{"role", "content"}, ...]`` -> (formatted text, last user message)."""
    if not history:
        return None, None
    lines, last_user = [], None
    for turn in history:
        who = "Étudiant" if turn["role"] == "user" else "Assistant"
        lines.append(f"{who}: {turn['content']}")
        if turn["role"] == "user":
            last_user = turn["content"]
    return "Historique de la conversation:\n" + "\n".join(lines), last_user


def _route_agent(message: str, student, course_id=None) -> str:
    """Course-scoped questions are about course content (Learning agent).
    Procedures (inscription, bourses, attestations...) go to the
    Administrative agent. Otherwise: enrolled -> Academic, else Orientation."""
    if course_id:
        return "learning"
    if is_administrative(message):
        return "administrative"
    if getattr(student, "student_status", None) == "enrolled":
        return "academic"
    return _DEFAULT_AGENT


def _prepare(message, history, student, course_id):
    program = getattr(student, "program", None)
    profile = {
        "student_status": getattr(student, "student_status", "prospective"),
        "academic_year": getattr(student, "academic_year", None),
        "program": getattr(program, "name", None),
    }
    history_text, last_user = _format_history(history)
    # A short follow-up ("et pour la chimie ?") is retrieved together with the
    # previous question so the right documents are still found.
    retrieval_query = f"{last_user} {message}" if last_user and len(message.split()) <= 5 else message
    pipeline = RAGPipeline(_route_agent(message, student, course_id))
    kwargs = dict(
        student_profile=profile,
        history=history_text,
        retrieval_query=retrieval_query,
        student_id=str(student.id) if course_id and student is not None else None,
        course_id=str(course_id) if course_id else None,
    )
    return pipeline, kwargs


def answer_chat(message: str, history=None, student=None, course_id=None) -> dict:
    """Grounded, cited answer: ``{"answer": str, "citations": [{"document", "page"}]}``.

    Greetings / thanks / capability questions get a direct reply instead of
    going through the sourced pipeline (which would refuse them).
    """
    reply = conversational_reply(classify_intent(message))
    if reply is not None:
        return {"answer": reply, "citations": []}
    pipeline, kwargs = _prepare(message, history, student, course_id)
    result = pipeline.run(message, **kwargs)
    return {"answer": result["answer"], "citations": result.get("citations", [])}


def answer_chat_stream(message: str, history=None, student=None, course_id=None):
    """Streaming counterpart: returns ``(token_iterator, chunks)``. Factual
    answers end with a "[groundedness_check: <bool>]" marker."""
    intent = classify_intent(message)
    if intent != FACTUAL:
        reply = conversational_reply(intent)
        if reply is not None:
            return iter([reply]), []
    pipeline, kwargs = _prepare(message, history, student, course_id)
    return pipeline.run(message, stream=True, **kwargs)
