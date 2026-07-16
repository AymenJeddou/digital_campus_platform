from importlib import import_module
from typing import Any

from app.core.config import settings


def _normalize_response(response: Any, message: str) -> dict[str, Any]:
    if isinstance(response, dict):
        answer = response.get("answer")
        if isinstance(answer, str):
            return {"answer": answer, "citations": response.get("citations", [])}

    if isinstance(response, str):
        return {"answer": response, "citations": []}

    return {"answer": _fallback_response(message), "citations": []}


def _fallback_response(message: str) -> str:
    return f"I received your message: '{message}'. RAG pipeline will be connected soon."


def generate_chat_response(message: str, session_id, student) -> dict[str, Any]:
    handler_path = getattr(settings, "RAG_PIPELINE_HANDLER", None)
    if not handler_path:
        return {"answer": _fallback_response(message), "citations": []}

    module_name, separator, attribute_name = handler_path.rpartition(":")
    if not separator:
        return {"answer": _fallback_response(message), "citations": []}

    try:
        module = import_module(module_name)
        handler = getattr(module, attribute_name)
        return _normalize_response(
            handler(message=message, session_id=session_id, student=student),
            message,
        )
    except Exception:
        return {"answer": _fallback_response(message), "citations": []}

def generate_chat_response_stream(message: str, session_id, student):
    handler_path = getattr(settings, "RAG_PIPELINE_HANDLER", None)
    if not handler_path:
        def _fallback():
            yield _fallback_response(message)
        return _fallback(), []

    module_name, separator, attribute_name = handler_path.rpartition(":")
    attribute_name += "_stream"
    try:
        module = import_module(module_name)
        handler = getattr(module, attribute_name)
        return handler(message=message, session_id=session_id, student=student)
    except Exception:
        def _fallback():
            yield _fallback_response(message)
        return _fallback(), []