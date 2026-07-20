"""Backend integration entrypoint for the RAG pipeline.

The backend's chat service dynamically imports a handler via the
``RAG_PIPELINE_HANDLER`` setting (``module:function``). Point it here:

    RAG_PIPELINE_HANDLER=ai.integration:answer_chat

This adapter turns the backend's call shape into a ``RAGPipeline`` call and
returns ``{"answer", "citations"}`` for the chat response.
"""

from ai.rag.intent import classify_intent, conversational_reply, FACTUAL
from ai.rag.pipeline import RAGPipeline

# Default agent when none is derived from the profile.
_DEFAULT_AGENT = "orientation"

# How many recent turns of a conversation to feed back into the pipeline.
_HISTORY_TURNS = 6


def _recent_history(session_id):
    """Fetch the recent turns of a chat session as (formatted_text, last_user_msg).

    Reads the backend's ``chat_messages`` table through the AI DB connection. The
    backend commits the *current* user message only after this call, so the fetch
    returns prior turns only — never the message being answered.
    """
    if not session_id:
        return None, None
    from sqlalchemy import text
    from ai.rag.db import get_session

    session = get_session()
    try:
        rows = session.execute(text("""
            SELECT role, content FROM chat_messages
            WHERE session_id = CAST(:sid AS uuid)
            ORDER BY created_at DESC
            LIMIT :lim
        """), {"sid": str(session_id), "lim": _HISTORY_TURNS}).fetchall()
    except Exception:
        return None, None
    finally:
        session.close()

    rows = list(reversed(rows))
    if not rows:
        return None, None

    lines, last_user = [], None
    for r in rows:
        who = "Étudiant" if r.role == "user" else "Assistant"
        lines.append(f"{who}: {r.content}")
        if r.role == "user":
            last_user = r.content
    return "Historique de la conversation:\n" + "\n".join(lines), last_user


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
    # Greetings / thanks / capability questions have no supporting document;
    # answer them directly instead of sending them through the sourced pipeline
    # (which would refuse). Conservative: anything factual falls through.
    intent = classify_intent(message)
    if intent != FACTUAL:
        reply = conversational_reply(intent)
        if reply is not None:
            return {"answer": reply, "citations": []}

    profile = {
        "student_status": getattr(student, "student_status", "prospective"),
        "academic_year": getattr(student, "academic_year", None),
    }
    agent_type = _route_agent(student)

    # Conversation memory: give the generator the recent turns, and for a short
    # follow-up ("et pour la chimie ?") augment the retrieval query with the
    # previous question so the right documents are still found.
    history, last_user = _recent_history(session_id)
    retrieval_query = message
    if last_user and len(message.split()) <= 5:
        retrieval_query = f"{last_user} {message}"

    result = RAGPipeline(agent_type).run(
        message,
        student_profile=profile,
        history=history,
        retrieval_query=retrieval_query,
    )
    return {"answer": result["answer"], "citations": result.get("citations", [])}
