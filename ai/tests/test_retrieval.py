"""Day 7 — End-to-end pipeline tests with all stages wired.

Tests the full flow: retrieval grader → generator → groundedness grader → citations.
All external calls (Gemini) are mocked.

Run from the repository root:
    pytest ai/tests/
"""

from unittest.mock import MagicMock, call, patch

import pytest

from ai.prompts.system_prompts import AGENT_TYPES, NO_INFO_SENTENCE
from ai.rag.generator import FAKE_CHUNKS
from ai.rag.pipeline import RAGPipeline

STUDENT_PROFILE = {"student_status": "enrolled", "academic_year": "L2"}


def _mock_genai_returning(text: str):
    """Helper: patch genai so generate_content always returns ``text``."""
    mock_resp = MagicMock()
    mock_resp.text = text
    mock_model = MagicMock()
    mock_model.generate_content.return_value = mock_resp
    mock_genai = MagicMock()
    mock_genai.GenerativeModel.return_value = mock_model
    return mock_genai


# --- 1. Full pipeline: grounded answer with citation ---------------------

@patch("ai.rag.groundedness_grader.genai", new_callable=lambda: type("G", (), {"GenerativeModel": None}))
@patch("ai.rag.retrieval_grader.genai")
@patch("ai.agents.base_agent.genai")
@patch("ai.rag.groundedness_grader.os.getenv", return_value="real_fake_key")
@patch("ai.rag.retrieval_grader.os.getenv", return_value="real_fake_key")
@patch("ai.agents.base_agent.os.getenv", return_value="real_fake_key")
def test_full_pipeline_grounded(
    _ge1, _ge2, _ge3, mock_base_genai, mock_grader_genai, mock_ground_genai
):
    answer_text = "Les cours commencent en octobre [Guide Académique FSB, p.12]."

    # base agent returns the answer
    fake_resp = MagicMock()
    fake_resp.text = answer_text
    mock_base_genai.GenerativeModel.return_value.generate_content.return_value = fake_resp

    # retrieval grader says "oui" (relevant)
    grader_resp = MagicMock()
    grader_resp.text = "oui"
    mock_grader_genai.GenerativeModel.return_value.generate_content.return_value = grader_resp

    # groundedness grader says "oui" (grounded)
    ground_resp = MagicMock()
    ground_resp.text = "oui"
    mock_ground_genai.GenerativeModel = MagicMock(
        return_value=MagicMock(generate_content=MagicMock(return_value=ground_resp))
    )

    pipeline = RAGPipeline("academic")
    result = pipeline.run("Quand commencent les cours?", FAKE_CHUNKS, STUDENT_PROFILE)

    assert result["answer"] == answer_text
    assert result["agent"] == "academic"
    assert result["chunks_used"] > 0
    assert isinstance(result["citations"], list)
    assert len(result["citations"]) >= 1


# --- 2. Hallucinated answer is replaced by NO_INFO_SENTENCE --------------

@patch("ai.rag.groundedness_grader.genai")
@patch("ai.rag.retrieval_grader.genai")
@patch("ai.agents.base_agent.genai")
@patch("ai.rag.groundedness_grader.os.getenv", return_value="real_fake_key")
@patch("ai.rag.retrieval_grader.os.getenv", return_value="real_fake_key")
@patch("ai.agents.base_agent.os.getenv", return_value="real_fake_key")
def test_hallucinated_answer_replaced(
    _ge1, _ge2, _ge3, mock_base_genai, mock_grader_genai, mock_ground_genai
):
    # Agent produces a hallucinated answer
    fake_resp = MagicMock()
    fake_resp.text = "La FSB a 5000 étudiants inscrits cette année."  # not in context
    mock_base_genai.GenerativeModel.return_value.generate_content.return_value = fake_resp

    grader_resp = MagicMock()
    grader_resp.text = "oui"
    mock_grader_genai.GenerativeModel.return_value.generate_content.return_value = grader_resp

    # Groundedness grader says "non" — hallucination
    ground_resp = MagicMock()
    ground_resp.text = "non"
    mock_ground_genai.GenerativeModel.return_value.generate_content.return_value = ground_resp

    pipeline = RAGPipeline("orientation")
    result = pipeline.run("Combien d'étudiants?", FAKE_CHUNKS, STUDENT_PROFILE)

    assert result["answer"] == NO_INFO_SENTENCE


# --- 3. All agent types instantiate without error ------------------------

@patch("ai.agents.base_agent.os.getenv", return_value="real_fake_key")
@patch("ai.agents.base_agent.genai")
@pytest.mark.parametrize("agent_type", AGENT_TYPES)
def test_all_agent_types_valid(_mock_genai, _mock_getenv, agent_type):
    pipeline = RAGPipeline(agent_type)
    assert pipeline.agent_type == agent_type


# --- 4. Empty chunks handled gracefully ----------------------------------

@patch("ai.rag.groundedness_grader.os.getenv", return_value="real_fake_key")
@patch("ai.rag.retrieval_grader.os.getenv", return_value="real_fake_key")
@patch("ai.agents.base_agent.os.getenv", return_value="real_fake_key")
@patch("ai.rag.groundedness_grader.genai")
@patch("ai.rag.retrieval_grader.genai")
@patch("ai.agents.base_agent.genai")
def test_empty_chunks(_mock_base, _mock_grader, _mock_ground, _ge1, _ge2, _ge3):
    fake_resp = MagicMock()
    fake_resp.text = NO_INFO_SENTENCE
    _mock_base.GenerativeModel.return_value.generate_content.return_value = fake_resp

    pipeline = RAGPipeline("administrative")
    result = pipeline.run("Question sans contexte.", [], STUDENT_PROFILE)

    assert "answer" in result
    assert "citations" in result
