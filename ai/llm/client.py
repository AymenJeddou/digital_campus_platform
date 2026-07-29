"""Provider-agnostic LLM client.

A single ``generate(prompt) -> str`` interface backed by either Google Gemini or
Mistral. The active provider is chosen by the ``LLM_PROVIDER`` env var, so
switching providers is configuration-only — no code change.

Env:
    LLM_PROVIDER   "gemini" (default) | "mistral"
    GEMINI_API_KEY / GEMINI_MODEL
    MISTRAL_API_KEY / MISTRAL_MODEL
"""

import logging
import os
import time
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Transient network hiccups (connection reset/disconnect) are common against a
# remote LLM API; retry a couple of times before surfacing an error rather than
# failing a user's chat on one blip.
_RETRIES = 2
_BACKOFF_SECONDS = 1.5


def _with_retries(call, what: str):
    last = None
    for attempt in range(_RETRIES + 1):
        try:
            return call()
        except Exception as e:  # noqa: BLE001
            name = type(e).__name__
            transient = any(
                t in name for t in ("ConnectError", "RemoteProtocolError", "ReadError",
                                     "ConnectTimeout", "ReadTimeout", "WriteError")
            )
            if not transient or attempt == _RETRIES:
                raise
            last = e
            logger.warning("Transient LLM error on %s (%s); retry %d/%d", what, name, attempt + 1, _RETRIES)
            time.sleep(_BACKOFF_SECONDS * (attempt + 1))
    raise last  # unreachable

# Load ai/.env regardless of the current working directory.
_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_MISTRAL_MODEL = "mistral-medium-latest"

# Default generation temperature (sourced answers favour consistency over
# variety); override per-call or via GENERATION_TEMPERATURE.
DEFAULT_TEMPERATURE = 0.2

_PLACEHOLDERS = {"your_gemini_api_key_here", "your_mistral_api_key_here", ""}


class BaseLLM:
    """Common interface: turn a prompt string into an answer string."""

    def generate(self, prompt: str, temperature: float | None = None) -> str:  # pragma: no cover - interface
        raise NotImplementedError

    def generate_stream(self, prompt: str, temperature: float | None = None):
        raise NotImplementedError


class GeminiClient(BaseLLM):
    def __init__(self, model: str = None):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key in _PLACEHOLDERS:
            raise ValueError(
                "GEMINI_API_KEY is not configured. Copy .env.example to .env "
                "and add your real key."
            )
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(
            model or os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
        )

    def generate(self, prompt: str, temperature: float | None = None) -> str:
        cfg = None
        if temperature is not None:
            import google.generativeai as genai
            cfg = genai.types.GenerationConfig(temperature=temperature)
        return self._model.generate_content(prompt, generation_config=cfg).text

    def generate_stream(self, prompt: str, temperature: float | None = None):
        cfg = None
        if temperature is not None:
            import google.generativeai as genai
            cfg = genai.types.GenerationConfig(temperature=temperature)
        response = self._model.generate_content(prompt, generation_config=cfg, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text


class MistralClient(BaseLLM):
    def __init__(self, model: str = None):
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key or api_key in _PLACEHOLDERS:
            raise ValueError(
                "MISTRAL_API_KEY is not configured. Copy .env.example to .env "
                "and add your real key."
            )
        from mistralai import Mistral

        self._client = Mistral(api_key=api_key)
        self._model = model or os.getenv("MISTRAL_MODEL", DEFAULT_MISTRAL_MODEL)

    def generate(self, prompt: str, temperature: float | None = None) -> str:
        def _call():
            return self._client.chat.complete(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                temperature=DEFAULT_TEMPERATURE if temperature is None else temperature,
            )
        resp = _with_retries(_call, "generate")
        return resp.choices[0].message.content

    def generate_stream(self, prompt: str, temperature: float | None = None):
        resp = self._client.chat.stream(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            temperature=DEFAULT_TEMPERATURE if temperature is None else temperature,
        )
        for chunk in resp:
            content = chunk.data.choices[0].delta.content
            if content:
                yield content


_PROVIDERS = {"gemini": GeminiClient, "mistral": MistralClient}


@lru_cache(maxsize=8)
def get_llm(model: str = None) -> BaseLLM:
    """Return an LLM client for the configured ``LLM_PROVIDER``.

    Cached per ``model`` so the client (and its ``.env`` read) is built once and
    reused — the generation model and the (separate) grader model each get their
    own cached client. This removes a per-call client construction + dotenv read.

    Args:
        model: Optional explicit model name (overrides the per-provider default
            and env var) — e.g. a cheaper model for a grader.

    Raises:
        ValueError: If the provider is unknown or its API key is not configured.
    """
    load_dotenv(_ENV_PATH)
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    if provider not in _PROVIDERS:
        raise ValueError(
            f"Unknown LLM_PROVIDER '{provider}'. Use one of {list(_PROVIDERS)}."
        )
    return _PROVIDERS[provider](model)
