"""Tests for the Day 5 retrieval grader.

All Gemini calls are mocked — no real API key needed.

Run from the repository root:
    pytest ai/tests/
"""

from unittest.mock import MagicMock, patch

import pytest

from ai.rag.retrieval_grader import filter_chunks, grade_retrieval

CHUNK_RELEVANT = {
    "chunk_id": "001",
    "text": "Les étudiants de L2 doivent s'inscrire avant le 15 octobre.",
    "source": "Guide FSB",
    "page": 12,
    "category": "academic",
    "score": 0.92,
}
CHUNK_IRRELEVANT = {
    "chunk_id": "002",
    "text": "La cafétéria est ouverte de 8h à 17h.",
    "source": "Guide FSB",
    "page": 45,
    "category": "campus_life",
    "score": 0.21,
}


# --- 1. grade_retrieval ---------------------------------------------------

@patch("ai.rag.retrieval_grader.os.getenv", return_value="real_fake_key")
@patch("ai.rag.retrieval_grader.genai")
def test_grade_relevant_chunk(mock_genai, _mock_getenv):
    mock_resp = MagicMock()
    mock_resp.text = "oui"
    mock_genai.GenerativeModel.return_value.generate_content.return_value = mock_resp

    result = grade_retrieval("Quand sont les inscriptions?", CHUNK_RELEVANT)
    assert result is True


@patch("ai.rag.retrieval_grader.os.getenv", return_value="real_fake_key")
@patch("ai.rag.retrieval_grader.genai")
def test_grade_irrelevant_chunk(mock_genai, _mock_getenv):
    mock_resp = MagicMock()
    mock_resp.text = "non"
    mock_genai.GenerativeModel.return_value.generate_content.return_value = mock_resp

    result = grade_retrieval("Quand sont les inscriptions?", CHUNK_IRRELEVANT)
    assert result is False


@patch("ai.rag.retrieval_grader.os.getenv", return_value="real_fake_key")
@patch("ai.rag.retrieval_grader.genai")
def test_grade_fails_open_on_api_error(mock_genai, _mock_getenv):
    mock_genai.GenerativeModel.return_value.generate_content.side_effect = Exception("timeout")

    result = grade_retrieval("Question?", CHUNK_RELEVANT)
    assert result is True  # fail open — keep the chunk


# --- 2. filter_chunks -----------------------------------------------------

@patch("ai.rag.retrieval_grader.os.getenv", return_value="real_fake_key")
@patch("ai.rag.retrieval_grader.genai")
def test_filter_keeps_relevant(mock_genai, _mock_getenv):
    mock_resp = MagicMock()
    mock_resp.text = "oui"
    mock_genai.GenerativeModel.return_value.generate_content.return_value = mock_resp

    result = filter_chunks("Inscriptions?", [CHUNK_RELEVANT, CHUNK_IRRELEVANT])
    assert CHUNK_RELEVANT in result


@patch("ai.rag.retrieval_grader.os.getenv", return_value="real_fake_key")
@patch("ai.rag.retrieval_grader.genai")
def test_filter_fallback_when_all_filtered(mock_genai, _mock_getenv):
    """If all chunks are graded out, the original list is returned."""
    mock_resp = MagicMock()
    mock_resp.text = "non"
    mock_genai.GenerativeModel.return_value.generate_content.return_value = mock_resp

    original = [CHUNK_RELEVANT, CHUNK_IRRELEVANT]
    result = filter_chunks("Question hors sujet?", original)
    assert result == original


def test_filter_empty_input():
    result = filter_chunks("Question?", [])
    assert result == []
