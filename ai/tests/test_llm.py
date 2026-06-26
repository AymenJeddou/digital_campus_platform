"""Tests for the provider-agnostic LLM client (ai.llm.client).

``load_dotenv`` is neutralised so these tests don't read a real ai/.env.
"""

import pytest

import ai.llm.client as client


@pytest.fixture(autouse=True)
def _no_dotenv(monkeypatch):
    monkeypatch.setattr(client, "load_dotenv", lambda *a, **k: None)


def test_unknown_provider_raises(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "not_a_provider")
    with pytest.raises(ValueError):
        client.get_llm()


def test_gemini_missing_key_raises(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(ValueError):
        client.get_llm()


def test_mistral_missing_key_raises(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mistral")
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    with pytest.raises(ValueError):
        client.get_llm()


def test_mistral_placeholder_key_raises(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mistral")
    monkeypatch.setenv("MISTRAL_API_KEY", "your_mistral_api_key_here")
    with pytest.raises(ValueError):
        client.get_llm()


def test_default_provider_is_gemini(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    # default provider = gemini -> missing gemini key raises (proves selection)
    with pytest.raises(ValueError) as exc:
        client.get_llm()
    assert "GEMINI_API_KEY" in str(exc.value)
