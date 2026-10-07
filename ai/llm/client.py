"""Provider-agnostic LLM client.

``generate(prompt, system=...) -> str`` / ``generate_stream(...)`` backed by
either Google Gemini (``google-genai``) or Mistral. The active provider is
chosen by ``LLM_PROVIDER``, so switching is configuration-only.

``system`` carries the trusted instructions (rules, student profile, retrieved
context); ``prompt`` carries only the student's text. Keeping them in separate
roles is what stops a question like "ignore the rules above..." from being read
as part of the instructions.

Env:
    LLM_PROVIDER   "gemini" (default) | "mistral"
    GEMINI_API_KEY / GEMINI_MODEL
    MISTRAL_API_KEY / MISTRAL_MODEL
    LLM_TIMEOUT_SECONDS (default 60)
"""

import logging
import os
import time
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load ai/.env regardless of the current working directory.
_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_MISTRAL_MODEL = "mistral-medium-latest"

# Sourced answers favour consistency over variety; override per call or via
# GENERATION_TEMPERATURE (see base_agent).
DEFAULT_TEMPERATURE = 0.2

_PLACEHOLDERS = {"your_gemini_api_key_here", "your_mistral_api_key_here", ""}

# Transient network hiccups are common against a remote LLM API; retry a
# couple of times before surfacing an error.
_RETRIES = 2
_BACKOFF_SECONDS = 1.5
_TRANSIENT = ("ConnectError", "RemoteProtocolError", "ReadError", "ConnectTimeout",
              "ReadTimeout", "WriteError", "ServiceUnavailable", "ServerError")


def _timeout_seconds() -> int:
    return int(os.getenv("LLM_TIMEOUT_SECONDS", "60"))


def _with_retries(call, what: str):
    for attempt in range(_RETRIES + 1):
        try:
            return call()
        except Exception as e:  # noqa: BLE001
            name = type(e).__name__
            if not any(t in name for t in _TRANSIENT) or attempt == _RETRIES:
                raise
            logger.warning("Transient LLM error on %s (%s); retry %d/%d", what, name, attempt + 1, _RETRIES)
            time.sleep(_BACKOFF_SECONDS * (attempt + 1))


def _api_key(name: str) -> str:
    key = os.getenv(name)
    if not key or key in _PLACEHOLDERS:
        raise ValueError(f"{name} is not configured. Copy .env.example to .env and add your real key.")
    return key


class GeminiClient:
    def __init__(self, model: str = None):
        api_key = _api_key("GEMINI_API_KEY")
        from google import genai
        from google.genai import types

        self._types = types
        self._client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=_timeout_seconds() * 1000),
        )
        self._model = model or os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)

    def _config(self, temperature, system):
        return self._types.GenerateContentConfig(
            temperature=DEFAULT_TEMPERATURE if temperature is None else temperature,
            system_instruction=system,
        )

    def generate(self, prompt: str, temperature: float | None = None, system: str | None = None) -> str:
        resp = _with_retries(
            lambda: self._client.models.generate_content(
                model=self._model, contents=prompt, config=self._config(temperature, system)),
            "generate",
        )
        return resp.text or ""

    def generate_stream(self, prompt: str, temperature: float | None = None, system: str | None = None):
        for chunk in self._client.models.generate_content_stream(
            model=self._model, contents=prompt, config=self._config(temperature, system)
        ):
            if chunk.text:
                yield chunk.text


class MistralClient:
    def __init__(self, model: str = None):
        api_key = _api_key("MISTRAL_API_KEY")
        from mistralai.client import Mistral

        self._client = Mistral(api_key=api_key, timeout_ms=_timeout_seconds() * 1000)
        self._model = model or os.getenv("MISTRAL_MODEL", DEFAULT_MISTRAL_MODEL)

    @staticmethod
    def _messages(prompt: str, system: str | None):
        messages = [{"role": "system", "content": system}] if system else []
        return messages + [{"role": "user", "content": prompt}]

    def generate(self, prompt: str, temperature: float | None = None, system: str | None = None) -> str:
        resp = _with_retries(
            lambda: self._client.chat.complete(
                model=self._model,
                messages=self._messages(prompt, system),
                temperature=DEFAULT_TEMPERATURE if temperature is None else temperature,
            ),
            "generate",
        )
        return resp.choices[0].message.content

    def generate_stream(self, prompt: str, temperature: float | None = None, system: str | None = None):
        resp = self._client.chat.stream(
            model=self._model,
            messages=self._messages(prompt, system),
            temperature=DEFAULT_TEMPERATURE if temperature is None else temperature,
        )
        for chunk in resp:
            content = chunk.data.choices[0].delta.content
            if content:
                yield content


_PROVIDERS = {"gemini": GeminiClient, "mistral": MistralClient}


@lru_cache(maxsize=8)
def get_llm(model: str = None):
    """Return a (cached) client for the configured ``LLM_PROVIDER``.

    Raises:
        ValueError: If the provider is unknown or its API key is not configured.
    """
    load_dotenv(_ENV_PATH)
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    if provider not in _PROVIDERS:
        raise ValueError(f"Unknown LLM_PROVIDER '{provider}'. Use one of {list(_PROVIDERS)}.")
    return _PROVIDERS[provider](model)
