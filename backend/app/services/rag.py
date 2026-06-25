from importlib import import_module
from app.core.config import settings


def _fallback_response(message: str) -> str:
    return f"I received your message: '{message}'. RAG pipeline will be connected soon."


def generate_chat_response(message: str, session_id, student) -> str:
    handler_path = getattr(settings, "RAG_PIPELINE_HANDLER", None)
    if not handler_path:
        return _fallback_response(message)

    module_name, separator, attribute_name = handler_path.rpartition(":")
    if not separator:
        return _fallback_response(message)

    try:
        module = import_module(module_name)
        handler = getattr(module, attribute_name)
        return handler(message=message, session_id=session_id, student=student)
    except Exception:
        return _fallback_response(message)