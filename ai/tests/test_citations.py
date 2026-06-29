"""Tests for the Day 4 citation formatter.

Run from the repository root:
    pytest ai/tests/
"""

from ai.rag.citation_formatter import format_citations

CHUNKS = [
    {"source": "Guide Académique FSB", "page": 12, "text": "Les étudiants de L2..."},
    {"source": "Guide d'Orientation FSB", "page": 3, "text": "La faculté propose..."},
]


# --- 1. Parsing inline markers -------------------------------------------

def test_single_citation_parsed():
    answer = "Les cours commencent en octobre [Guide Académique FSB, p.12]."
    result = format_citations(answer, CHUNKS)
    assert result["answer"] == answer
    assert len(result["citations"]) == 1
    assert result["citations"][0]["document"] == "Guide Académique FSB"
    assert result["citations"][0]["page"] == 12


def test_multiple_citations_parsed():
    answer = (
        "La FSB propose des licences [Guide d'Orientation FSB, p.3] "
        "et des masters [Guide Académique FSB, p.12]."
    )
    result = format_citations(answer, CHUNKS)
    assert len(result["citations"]) == 2


def test_duplicate_citations_deduplicated():
    answer = (
        "Voir [Guide FSB, p.5] et aussi [Guide FSB, p.5] pour plus d'informations."
    )
    result = format_citations(answer, [])
    assert len(result["citations"]) == 1


def test_unknown_page_marker():
    answer = "Information disponible [Guide FSB, p.?]."
    result = format_citations(answer, [])
    assert result["citations"][0]["page"] is None


# --- 2. Fallback when no citation marker -----------------------------------

def test_fallback_uses_top_chunk_when_no_marker():
    answer = "Les inscriptions sont ouvertes."
    result = format_citations(answer, CHUNKS)
    assert len(result["citations"]) == 1
    assert result["citations"][0]["document"] == "Guide Académique FSB"
    assert result["citations"][0]["page"] == 12


def test_no_fallback_when_no_chunks_and_no_marker():
    answer = "Aucune information trouvée."
    result = format_citations(answer, [])
    assert result["citations"] == []


# --- 3. Answer is preserved unchanged ------------------------------------

def test_answer_unchanged():
    answer = "Réponse sans citation."
    result = format_citations(answer, CHUNKS)
    assert result["answer"] == answer
