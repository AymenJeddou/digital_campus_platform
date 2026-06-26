"""Provider-agnostic LLM client.

A single ``generate(prompt) -> str`` interface backed by either Google Gemini or
Mistral. The active provider is chosen by the ``LLM_PROVIDER`` env var, so
switching providers is configuration-only — no code change.

Env:
    LLM_PROVIDER   "gemini" (default) | "mistral"
    GEMINI_API_KEY / GEMINI_MODEL
    MISTRAL_API_KEY / MISTRAL_MODEL
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load ai/.env regardless of the current working directory.
_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_MISTRAL_MODEL = "mistral-medium-latest"

_PLACEHOLDERS = {"your_gemini_api_key_here", "your_mistral_api_key_here", ""}


class BaseLLM:
    """Common interface: turn a prompt string into an answer string."""

    def generate(self, prompt: str) -> str:  # pragma: no cover - interface
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

    def generate(self, prompt: str) -> str:
        return self._model.generate_content(prompt).text


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

    def generate(self, prompt: str) -> str:
        resp = self._client.chat.complete(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.choices[0].message.content


_PROVIDERS = {"gemini": GeminiClient, "mistral": MistralClient}


def get_llm(model: str = None) -> BaseLLM:
    """Return an LLM client for the configured ``LLM_PROVIDER``.

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
