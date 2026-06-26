"""Day 5 tests — retrieval grader (score threshold)."""

from unittest.mock import MagicMock, patch

from ai.prompts.system_prompts import NO_INFO_SENTENCE
from ai.rag.retrieval_grader import filter_chunks, grade_retrieval


def _chunk(score=None):
    c = {"text": "t", "title": "Doc", "source": "doc.md", "page": 1, "category": "orientation"}
    if score is not None:
        c["score"] = score
    return c


def _mock_llm(text="Réponse simulée."):
    llm = MagicMock()
    llm.generate.return_value = text
    return llm


# --- grade_retrieval -------------------------------------------------------

def test_high_score_passes():
    assert grade_retrieval("q", _chunk(0.91)) is True


def test_low_score_fails():
    assert grade_retrieval("q", _chunk(0.2)) is False


def test_missing_score_is_kept():
    assert grade_retrieval("q", _chunk(None)) is True


def test_custom_threshold_respected():
    assert grade_retrieval("q", _chunk(0.6), threshold=0.7) is False
    assert grade_retrieval("q", _chunk(0.8), threshold=0.7) is True


# --- filter_chunks ---------------------------------------------------------

def test_filter_keeps_passers_drops_failers():
    chunks = [_chunk(0.9), _chunk(0.1), _chunk(0.55)]
    kept = filter_chunks("q", chunks)
    assert len(kept) == 2
    assert all(c["score"] >= 0.5 for c in kept)


# --- pipeline integration --------------------------------------------------

@patch("ai.agents.base_agent.get_llm")
def test_pipeline_refuses_when_all_chunks_weak(mock_get_llm):
    mock_get_llm.return_value = _mock_llm("should not be called")
    from ai.rag.pipeline import RAGPipeline

    pipeline = RAGPipeline("orientation")
    result = pipeline.run("Une question", chunks=[_chunk(0.1), _chunk(0.2)])

    assert result["answer"] == NO_INFO_SENTENCE
    assert result["chunks_used"] == 0
    assert result["citations"] == []
    mock_get_llm.return_value.generate.assert_not_called()  # LLM never invoked


@patch("ai.agents.base_agent.get_llm")
def test_pipeline_generates_with_only_passing_chunks(mock_get_llm):
    mock_get_llm.return_value = _mock_llm("Réponse simulée.")
    from ai.rag.pipeline import RAGPipeline

    pipeline = RAGPipeline("orientation")
    result = pipeline.run("Une question", chunks=[_chunk(0.9), _chunk(0.1)])

    # only the high-score chunk should have reached generation
    assert result["answer"] == "Réponse simulée."
    assert result["chunks_used"] == 1
