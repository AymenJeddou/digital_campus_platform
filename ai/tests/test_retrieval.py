"""Day 3 tests — pipeline wired to the semantic search layer.

Verify that ``RAGPipeline.run`` retrieves chunks from ``src.search.retriever``
when none are passed, forwards ``top_k`` / ``category_filter``, and still works
when chunks are supplied explicitly. The LLM is mocked via
``ai.agents.base_agent.get_llm`` — no real API key needed.
"""

from unittest.mock import MagicMock, patch

from src.search.retriever import retrieve


def _mock_llm(text="Réponse simulée."):
    llm = MagicMock()
    llm.generate.return_value = text
    return llm


# --- 1. The mock retriever honours the agreed schema -----------------------

def test_retriever_returns_schema():
    out = retrieve("Quelles licences à la FSB?", top_k=3)
    assert isinstance(out, list) and out
    for field in ("chunk_id", "text", "title", "source", "page", "category", "score"):
        assert field in out[0]
    assert 0.0 <= out[0]["score"] <= 1.0


# --- 2. Pipeline retrieves when no chunks are passed -----------------------

@patch("ai.agents.base_agent.get_llm")
def test_pipeline_retrieves_and_generates(mock_get_llm):
    mock_get_llm.return_value = _mock_llm("Réponse simulée.")
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

    mock_ret.assert_called_once()
    _args, kwargs = mock_ret.call_args
    assert kwargs["top_k"] == 4
    assert kwargs["category_filter"] == ["orientation"]
    assert result["answer"] == "Réponse simulée."
    assert result["chunks_used"] == len(fake_chunks)


# --- 3. Explicit chunks bypass retrieval -----------------------------------

@patch("ai.agents.base_agent.get_llm")
def test_pipeline_explicit_chunks_skip_retrieval(mock_get_llm):
    mock_get_llm.return_value = _mock_llm("OK")
    from ai.rag.pipeline import RAGPipeline

    with patch("src.search.retriever.retrieve") as mock_ret:
        pipeline = RAGPipeline("academic")
        pipeline.run("Une question", chunks=[{"text": "x", "source": "s.md", "page": 1}])

    mock_ret.assert_not_called()
