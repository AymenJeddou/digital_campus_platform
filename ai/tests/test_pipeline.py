"""Tests for the generation pipeline.

The LLM is mocked by patching ``ai.agents.base_agent.get_llm``, so no real API
key (Gemini or Mistral) is required.

Run from the repository root:

    pytest ai/tests/
"""

from unittest.mock import MagicMock, patch

import pytest

from ai.agents.base_agent import BaseAgent
from ai.rag.generator import FAKE_CHUNKS
from ai.rag.pipeline import RAGPipeline


def _mock_llm(text="Réponse simulée."):
    """A fake LLM client whose generate() returns a fixed string."""
    llm = MagicMock()
    llm.generate.return_value = text
    return llm


# --- 1. _format_chunks -----------------------------------------------------

def test_format_chunks_empty():
    assert BaseAgent._format_chunks([]) == "Aucun contexte disponible."


def test_format_chunks_single():
    out = BaseAgent._format_chunks(
        [{"source": "Guide FSB", "page": 7, "text": "Bonjour le monde."}]
    )
    assert "Guide FSB" in out
    assert "p.7" in out
    assert "Bonjour le monde." in out


def test_format_chunks_multiple_has_separator():
    out = BaseAgent._format_chunks(FAKE_CHUNKS)
    assert "---" in out


# --- 2. Full pipeline with a mocked LLM ------------------------------------

@patch("ai.agents.base_agent.get_llm")
def test_pipeline_run_mocked(mock_get_llm):
    mock_get_llm.return_value = _mock_llm("Réponse simulée.")

    pipeline = RAGPipeline("orientation")
    result = pipeline.run(
        "Quelles sont les licences disponibles?",
        student_profile={"student_status": "prospective", "academic_year": None},
        chunks=FAKE_CHUNKS,
    )

    for key in ("answer", "agent", "chunks_used", "raw_response"):
        assert key in result
    assert result["answer"] == "Réponse simulée."
    assert result["chunks_used"] == len(FAKE_CHUNKS)
    assert result["agent"] == "orientation"


# --- 3. Invalid agent type -------------------------------------------------

def test_pipeline_invalid_agent_raises():
    with pytest.raises(ValueError):
        RAGPipeline("invalid_agent")
