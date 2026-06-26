"""Day 6 tests — groundedness grader."""

from unittest.mock import MagicMock, patch

from ai.prompts.system_prompts import NO_INFO_SENTENCE
from ai.rag.groundedness_grader import grade_groundedness

CHUNKS = [{"title": "Guide FSB", "source": "g.md", "page": 3,
           "text": "Trois licences: Informatique, Mathématiques, Physique."}]


def _judge(verdict):
    llm = MagicMock()
    llm.generate.return_value = verdict
    return llm


# --- grade_groundedness ----------------------------------------------------

def test_grounded_verdict_oui_passes():
    assert grade_groundedness("Trois licences.", CHUNKS, llm=_judge("OUI")) is True


def test_ungrounded_verdict_non_blocks():
    assert grade_groundedness("Licence de Médecine.", CHUNKS, llm=_judge("NON")) is False


def test_garbage_verdict_blocks():
    # fail-safe: anything not starting with OUI is treated as not grounded
    assert grade_groundedness("X", CHUNKS, llm=_judge("peut-être")) is False


def test_no_chunks_blocks():
    assert grade_groundedness("X", [], llm=_judge("OUI")) is False


# --- pipeline integration --------------------------------------------------

@patch("ai.rag.pipeline.grade_groundedness", return_value=False)
@patch("ai.agents.base_agent.get_llm")
def test_pipeline_blocks_ungrounded_answer(mock_get_llm, _mock_grounded):
    llm = MagicMock()
    llm.generate.return_value = "Une réponse inventée [Guide FSB, p.3]."
    mock_get_llm.return_value = llm
    from ai.rag.pipeline import RAGPipeline

    result = RAGPipeline("orientation").run("Une question", chunks=CHUNKS)
    assert result["answer"] == NO_INFO_SENTENCE
    assert result["citations"] == []


@patch("ai.rag.pipeline.grade_groundedness", return_value=True)
@patch("ai.agents.base_agent.get_llm")
def test_pipeline_passes_grounded_answer(mock_get_llm, _mock_grounded):
    llm = MagicMock()
    llm.generate.return_value = "Trois licences [Guide FSB, p.3]."
    mock_get_llm.return_value = llm
    from ai.rag.pipeline import RAGPipeline

    result = RAGPipeline("orientation").run("Une question", chunks=CHUNKS)
    assert result["answer"] == "Trois licences [Guide FSB, p.3]."
    assert result["citations"] == [{"document": "Guide FSB", "page": 3}]
