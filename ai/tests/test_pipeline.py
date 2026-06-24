"""Tests for the Day 2 generation pipeline.

All tests run without a real ``GEMINI_API_KEY`` — the Gemini client and the
environment lookup are mocked with ``unittest.mock.patch``.

Run from the repository root:

    pytest ai/tests/
"""

from unittest.mock import MagicMock, patch

import pytest

from ai.agents.base_agent import BaseAgent
from ai.rag.generator import FAKE_CHUNKS
from ai.rag.pipeline import RAGPipeline

PLACEHOLDER = "your_gemini_api_key_here"


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


# --- 2 & 3. API key validation at __init__ ---------------------------------

@patch("ai.agents.base_agent.os.getenv", return_value=None)
def test_missing_api_key_raises(_mock_getenv):
    from ai.agents.orientation_agent import OrientationAgent

    with pytest.raises(ValueError):
        OrientationAgent()


@patch("ai.agents.base_agent.os.getenv", return_value=PLACEHOLDER)
def test_placeholder_api_key_raises(_mock_getenv):
    from ai.agents.academic_agent import AcademicAgent

    with pytest.raises(ValueError):
        AcademicAgent()


# --- 4. Full pipeline with mocked Gemini -----------------------------------

@patch("ai.agents.base_agent.genai")
@patch("ai.agents.base_agent.os.getenv", return_value="real_fake_key")
def test_pipeline_run_mocked(_mock_getenv, mock_genai):
    fake_response = MagicMock()
    fake_response.text = "Réponse simulée."
    mock_genai.GenerativeModel.return_value.generate_content.return_value = (
        fake_response
    )

    pipeline = RAGPipeline("orientation")
    result = pipeline.run(
        "Quelles sont les licences disponibles?",
        FAKE_CHUNKS,
        {"student_status": "prospective", "academic_year": None},
    )

    for key in ("answer", "agent", "chunks_used", "raw_response"):
        assert key in result
    assert result["answer"] == "Réponse simulée."
    assert result["chunks_used"] == len(FAKE_CHUNKS)
    assert result["agent"] == "orientation"


# --- 5. Invalid agent type -------------------------------------------------

def test_pipeline_invalid_agent_raises():
    with pytest.raises(ValueError):
        RAGPipeline("invalid_agent")
