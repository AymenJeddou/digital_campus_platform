"""Day 3 tests — pipeline wired to the semantic search layer.

Verify that ``RAGPipeline.run`` retrieves chunks from ``src.search.retriever``
when none are passed, forwards ``top_k`` / ``category_filter``, and still works
when chunks are supplied explicitly. Gemini and the env lookup are mocked, so no
real API key is needed.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.search.retriever import retrieve


# --- 1. The mock retriever honours the agreed schema -----------------------

def test_retriever_returns_schema():
    out = retrieve("Quelles licences à la FSB?", top_k=3)
    assert isinstance(out, list) and out
    for field in ("chunk_id", "text", "title", "source", "page", "category", "score"):
        assert field in out[0]
    assert 0.0 <= out[0]["score"] <= 1.0


# --- 2. Pipeline retrieves when no chunks are passed -----------------------

@patch("ai.agents.base_agent.genai")
@patch("ai.agents.base_agent.os.getenv", return_value="real_fake_key")
def test_pipeline_retrieves_and_generates(_getenv, mock_genai):
    mock_genai.GenerativeModel.return_value.generate_content.return_value.text = (
        "Réponse simulée."
    )
    fake_chunks = [{
        "chunk_id": "c1", "text": "Trois licences sont proposées.",
        "title": "Guide FSB", "source": "guide.md", "page": 2,
        "category": "orientation", "score": 0.9,
    }]

    from ai.rag.pipeline import RAGPipeline

    with patch("src.search.retriever.retrieve", return_value=fake_chunks) as mock_ret:
        pipeline = RAGPipeline("orientation")
        result = pipeline.run(
            "Quelles licences sont disponibles?",
            student_profile={"student_status": "prospective", "academic_year": None},
            top_k=4,
            category_filter=["orientation"],
        )

    # retriever was called with the question and forwarded params
    mock_ret.assert_called_once()
    args, kwargs = mock_ret.call_args
    assert kwargs["top_k"] == 4
    assert kwargs["category_filter"] == ["orientation"]
    # answer flowed through and counted the retrieved chunks
    assert result["answer"] == "Réponse simulée."
    assert result["chunks_used"] == len(fake_chunks)


# --- 3. Explicit chunks bypass retrieval -----------------------------------

@patch("ai.agents.base_agent.genai")
@patch("ai.agents.base_agent.os.getenv", return_value="real_fake_key")
def test_pipeline_explicit_chunks_skip_retrieval(_getenv, mock_genai):
    mock_genai.GenerativeModel.return_value.generate_content.return_value.text = "OK"
    from ai.rag.pipeline import RAGPipeline

    with patch("src.search.retriever.retrieve") as mock_ret:
        pipeline = RAGPipeline("academic")
        pipeline.run("Une question", chunks=[{"text": "x", "source": "s.md", "page": 1}])

    mock_ret.assert_not_called()
