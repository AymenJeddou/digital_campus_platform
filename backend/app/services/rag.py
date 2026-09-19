import logging
from importlib import import_module
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

# Shown to the user when the RAG pipeline raises. NOT a "feature not built"
# message — a real failure must read as an error the user can retry, and the
# real cause is logged with a traceback for the operator.
_ERROR_MESSAGE = "Une erreur est survenue lors de la génération de la réponse. Veuillez réessayer."
# Shown only when no pipeline handler is configured at all (a deployment/config
# issue, not a runtime failure).
_NOT_CONFIGURED = "L'assistant n'est pas encore configuré (RAG_PIPELINE_HANDLER manquant)."


def _normalize_response(response: Any, message: str) -> dict[str, Any]:
    if isinstance(response, dict):
        answer = response.get("answer")
        if isinstance(answer, str):
            return {"answer": answer, "citations": response.get("citations", [])}

    if isinstance(response, str):
        return {"answer": response, "citations": []}

    logger.error("RAG handler returned an unexpected shape: %r", type(response))
    return {"answer": _ERROR_MESSAGE, "citations": []}


def generate_chat_response(message: str, session_id, student, course_id=None) -> dict[str, Any]:
    handler_path = getattr(settings, "RAG_PIPELINE_HANDLER", None)
    if not handler_path or ":" not in handler_path:
        logger.error("RAG_PIPELINE_HANDLER not configured: %r", handler_path)
        return {"answer": _NOT_CONFIGURED, "citations": []}

    module_name, _, attribute_name = handler_path.rpartition(":")
    try:
        module = import_module(module_name)
        handler = getattr(module, attribute_name)
        return _normalize_response(
            handler(message=message, session_id=session_id, student=student, course_id=course_id),
            message,
        )
    except Exception:
        # Log the REAL cause with a traceback; show the user a retryable error,
        # never a "not built yet" placeholder.
        logger.exception("RAG pipeline failed for message %r", message[:80])
        return {"answer": _ERROR_MESSAGE, "citations": []}


def generate_chat_response_stream(message: str, session_id, student, course_id=None):
    handler_path = getattr(settings, "RAG_PIPELINE_HANDLER", None)
    if not handler_path or ":" not in handler_path:
        logger.error("RAG_PIPELINE_HANDLER not configured: %r", handler_path)
        def _msg():
            yield _NOT_CONFIGURED
        return _msg(), []

    module_name, _, attribute_name = handler_path.rpartition(":")
    attribute_name += "_stream"
    try:
        module = import_module(module_name)
        handler = getattr(module, attribute_name)
        return handler(message=message, session_id=session_id, student=student, course_id=course_id)
    except Exception:
        logger.exception("RAG streaming pipeline failed for message %r", message[:80])
        def _err():
            yield _ERROR_MESSAGE
        return _err(), []