"""Day 4 tests — citation formatting.

Pure string parsing; no API key needed.
"""

from ai.prompts.system_prompts import NO_INFO_SENTENCE
from ai.rag.citation_formatter import format_citations

CHUNKS = [
    {"title": "Guide d'Orientation FSB", "source": "guide.md", "page": 3},
    {"title": "Guide Académique FSB", "source": "acad.md", "page": 12},
]


def test_single_citation_parsed():
    ans = "La FSB propose trois licences [Guide d'Orientation FSB, p.3]."
    out = format_citations(ans, CHUNKS)
    assert out["citations"] == [{"document": "Guide d'Orientation FSB", "page": 3}]
    assert out["answer"] == ans  # inline markers preserved


def test_multiple_citations():
    ans = ("Inscription avant le 15 octobre [Guide Académique FSB, p.12]. "
           "Trois licences [Guide d'Orientation FSB, p.3].")
    out = format_citations(ans, CHUNKS)
    assert {"document": "Guide Académique FSB", "page": 12} in out["citations"]
    assert {"document": "Guide d'Orientation FSB", "page": 3} in out["citations"]
    assert len(out["citations"]) == 2


def test_duplicate_citations_collapsed():
    ans = ("A [Guide d'Orientation FSB, p.3]. B [Guide d'Orientation FSB, p.3].")
    out = format_citations(ans, CHUNKS)
    assert out["citations"] == [{"document": "Guide d'Orientation FSB", "page": 3}]


def test_tolerant_spacing():
    ans = "Texte [Guide Académique FSB, p. 12] suite."
    out = format_citations(ans, CHUNKS)
    assert out["citations"] == [{"document": "Guide Académique FSB", "page": 12}]


def test_no_citation_falls_back_to_top_chunk():
    ans = "La faculté propose plusieurs licences scientifiques."
    out = format_citations(ans, CHUNKS)
    # top chunk (CHUNKS[0]) attached as fallback
    assert out["citations"] == [{"document": "Guide d'Orientation FSB", "page": 3}]


def test_refusal_has_no_citations():
    out = format_citations(NO_INFO_SENTENCE, CHUNKS)
    assert out["citations"] == []


def test_no_chunks_no_fallback():
    out = format_citations("Réponse sans contexte.", [])
    assert out["citations"] == []
