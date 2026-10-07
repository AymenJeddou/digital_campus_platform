import logging
from importlib import import_module
from typing import Any, Callable

from app.core.config import settings

logger = logging.getLogger(__name__)

# Shown to the user when the RAG pipeline raises. The real cause is logged
# with a traceback for the operator.
ERROR_MESSAGE = "Une erreur est survenue lors de la génération de la réponse. Veuillez réessayer."
# Shown only when no pipeline handler is configured at all (a deployment issue).
_NOT_CONFIGURED = "L'assistant n'est pas encore configuré (RAG_PIPELINE_HANDLER manquant)."


def _handler(suffix: str = "") -> Callable | None:
    """Resolve RAG_PIPELINE_HANDLER (``module:function``) + optional suffix."""
    path = settings.RAG_PIPELINE_HANDLER
    if not path or ":" not in path:
        logger.error("RAG_PIPELINE_HANDLER not configured: %r", path)
        return None
    module_name, _, attribute = path.rpartition(":")
    return getattr(import_module(module_name), attribute + suffix)


def generate_chat_response(message: str, student, history: list[dict], course_id=None) -> dict[str, Any]:
    try:
        handler = _handler()
        if handler is None:
            return {"answer": _NOT_CONFIGURED, "citations": []}
        response = handler(message=message, history=history, student=student, course_id=course_id)
    except Exception:
        logger.exception("RAG pipeline failed for message %r", message[:80])
        return {"answer": ERROR_MESSAGE, "citations": []}
    if isinstance(response, dict) and isinstance(response.get("answer"), str):
        return {"answer": response["answer"], "citations": response.get("citations", [])}
    logger.error("RAG handler returned an unexpected shape: %r", type(response))
    return {"answer": ERROR_MESSAGE, "citations": []}


def generate_chat_response_stream(message: str, student, history: list[dict], course_id=None):
    """Return ``(token_iterator, chunks)``. Never raises: failures become a
    one-token stream carrying the user-facing error message."""
    try:
        handler = _handler("_stream")
        if handler is None:
            return iter([_NOT_CONFIGURED]), []
        return handler(message=message, history=history, student=student, course_id=course_id)
    except Exception:
        logger.exception("RAG streaming pipeline failed for message %r", message[:80])
        return iter([ERROR_MESSAGE]), []
