"""Tests for the Day 6 groundedness grader.

All Gemini calls are mocked — no real API key needed.

Run from the repository root:
    pytest ai/tests/
"""

from unittest.mock import MagicMock, patch

from ai.prompts.system_prompts import NO_INFO_SENTENCE
from ai.rag.groundedness_grader import grade_groundedness

CHUNKS = [
    {
        "source": "Guide Académique FSB",
        "page": 12,
        "text": "Les étudiants de L2 doivent s'inscrire avant le 15 octobre.",
    }
]


# --- 1. Grounded answer --------------------------------------------------

@patch("ai.rag.groundedness_grader.os.getenv", return_value="real_fake_key")
@patch("ai.rag.groundedness_grader.genai")
def test_grounded_answer_returns_true(mock_genai, _mock_getenv):
    mock_resp = MagicMock()
    mock_resp.text = "oui"
    mock_genai.GenerativeModel.return_value.generate_content.return_value = mock_resp

    result = grade_groundedness(
        "Les inscriptions sont avant le 15 octobre [Guide Académique FSB, p.12].",
        CHUNKS,
    )
    assert result is True


# --- 2. Hallucinated answer -----------------------------------------------

@patch("ai.rag.groundedness_grader.os.getenv", return_value="real_fake_key")
@patch("ai.rag.groundedness_grader.genai")
def test_hallucinated_answer_returns_false(mock_genai, _mock_getenv):
    mock_resp = MagicMock()
    mock_resp.text = "non"
    mock_genai.GenerativeModel.return_value.generate_content.return_value = mock_resp

    result = grade_groundedness(
        "Les inscriptions sont disponibles toute l'année.",  # not in context
        CHUNKS,
    )
    assert result is False


# --- 3. Refusal sentence is always grounded --------------------------------

def test_no_info_sentence_always_grounded():
    # NO_INFO_SENTENCE should pass without any API call
    result = grade_groundedness(NO_INFO_SENTENCE, CHUNKS)
    assert result is True


# --- 4. Fail open on API error --------------------------------------------

@patch("ai.rag.groundedness_grader.os.getenv", return_value="real_fake_key")
@patch("ai.rag.groundedness_grader.genai")
def test_fails_open_on_api_error(mock_genai, _mock_getenv):
    mock_genai.GenerativeModel.return_value.generate_content.side_effect = Exception("quota exceeded")

    result = grade_groundedness("Réponse quelconque.", CHUNKS)
    assert result is True  # fail open — don't block valid answers
