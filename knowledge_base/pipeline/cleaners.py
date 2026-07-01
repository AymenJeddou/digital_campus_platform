"""
Type-specific cleaners.

Each public function takes a *body* string (header already stripped by
`frontmatter.parse`) and returns cleaned markdown. All cleaners share one rule:

    NEVER delete `[p.N]` page markers and NEVER delete heading lines (`#`, `##`).
    The chunker needs them to track pages and section boundaries.

Cleaners:
  - clean_web      : HTML-to-markdown web pages (FSB site, national news pages)
  - clean_course   : program curricula / "maquettes" (heavy tables, exploded cells)
  - clean_arabic   : OCR'd Arabic docs (orientation guide, admin form templates)
  - clean_generic  : fallback / already-tidy text
"""

from __future__ import annotations

import re


# --------------------------------------------------------------------------- #
# Shared helpers
# --------------------------------------------------------------------------- #

_IMG = re.compile(r"!\[[^\]]*\]\([^)]*\)")          # ![alt](url)
_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")          # [text](url) -> text
_HTML_TAG = re.compile(r"<[^>]+>")
_PAGE_MARKER = re.compile(r"^\s*\[p\.\d+\]\s*$")
_HEADING = re.compile(r"^\s{0,3}#{1,6}\s")


def _is_protected(line: str) -> bool:
    """Lines the chunker depends on — keep them no matter what."""
    return bool(_PAGE_MARKER.match(line) or _HEADING.match(line))


def _strip_inline(text: str) -> str:
    text = _IMG.sub("", text)
    text = _LINK.sub(r"\1", text)
    text = text.replace("<br>", " ").replace("<br/>", " ").replace("<br />", " ")
    text = _HTML_TAG.sub("", text)
    return text


def _collapse_blanks(text: str) -> str:
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # trim trailing spaces per line
    text = "\n".join(l.rstrip() for l in text.split("\n"))
    return text.strip()


def base_clean(body: str) -> str:
    """Inline markdown/HTML cleanup applied before every specialised cleaner."""
    body = _strip_inline(body)
    return _collapse_blanks(body)


# --------------------------------------------------------------------------- #
# Professor roster removal (per the "drop professor listings" decision)
# --------------------------------------------------------------------------- #

# Academic grade tokens that mark the right-hand column of a roster table.
_GRADE = re.compile(
    r"^(Prof|MC|MCF|MA|MA/C\.E|A|C\.E|PES|PPETC|PPHCTC|PPEHCTC|PPE?T?C)\b",
    re.IGNORECASE,
)
_ROSTER_HEADER = {"n°", "no", "nom et prénom", "nom et prenom", "grade", "nom", "prénom"}


def strip_professor_roster(text: str) -> str:
    """
    Remove `N° / Name / Grade` listings that appear (exploded onto separate
    lines) inside department web pages. Keeps everything else: department head,
    formations, research lab, etc.

    Strategy: a roster shows up as many lone-integer lines, each followed within
    a couple of lines by a grade token. We drop the header tokens, the integer
    "rank" lines, the name line(s) between an integer and its grade, and the
    grade line itself.
    """
    lines = text.split("\n")
    drop = [False] * len(lines)

    for i, line in enumerate(lines):
        s = line.strip()
        if s.lower() in _ROSTER_HEADER:
            drop[i] = True
            continue
        if re.fullmatch(r"\d{1,3}", s):
            # a rank number: drop it and the following lines up to a grade token
            j = i
            while j < len(lines) and j < i + 4:
                drop[j] = True
                if _GRADE.match(lines[j].strip()):
                    break
                j += 1

    kept = [l for l, d in zip(lines, drop) if not d]
    return _collapse_blanks("\n".join(kept))


# --------------------------------------------------------------------------- #
# Web pages
# --------------------------------------------------------------------------- #

# Sidebar / boilerplate phrases seen on scraped news & FSB pages.
_WEB_NOISE = re.compile(
    r"^(en continu|lire aussi|articles? similaires?|partager|commentaires?|"
    r"bourse de tunis|ins\s*:|sur le m[êe]me sujet|tags?\s*:)",
    re.IGNORECASE,
)


def clean_web(body: str) -> str:
    body = base_clean(body)
    body = strip_professor_roster(body)

    out = []
    for line in body.split("\n"):
        s = line.strip()
        if _is_protected(line):
            out.append(line)
            continue
        if _WEB_NOISE.match(s):
            continue
        # leftover author/title meta that slipped past the header parser
        if re.match(r"^\*\*(title|author|source)\*\*", s, re.IGNORECASE):
            continue
        # empty bullet or pure-punctuation line
        if re.fullmatch(r"[-*•·.\s|]*", s):
            continue
        out.append(line)
    return _collapse_blanks("\n".join(out))


# --------------------------------------------------------------------------- #
# Course curricula / maquettes
# --------------------------------------------------------------------------- #

def _is_short_cell(line: str) -> bool:
    """A line that looks like a single exploded table cell (<=3 words)."""
    s = line.strip()
    if not s or _is_protected(line):
        return False
    if "|" in s:                       # already a joined table row
        return False
    return len(s.split()) <= 3


def clean_course(body: str) -> str:
    """
    Maquette PDFs often explode every table cell onto its own line:

        Cours
        TD
        TP

    We re-flow runs of such short lines into a single pipe-separated line
    (`Cours | TD | TP`) so a chunk keeps numbers next to their labels. This is
    a readability heuristic, not a faithful grid reconstruction — perfect table
    structure is out of scope and error-prone.
    """
    body = base_clean(body)

    out: list[str] = []
    buffer: list[str] = []

    def flush():
        if buffer:
            out.append(" | ".join(buffer))
            buffer.clear()

    for line in body.split("\n"):
        if _is_short_cell(line):
            buffer.append(line.strip())
            if len(buffer) >= 14:       # cap row width so lines stay sane
                flush()
        else:
            flush()
            out.append(line)
    flush()
    return _collapse_blanks("\n".join(out))


# --------------------------------------------------------------------------- #
# Arabic OCR (orientation guide + administrative form templates)
# --------------------------------------------------------------------------- #

_ARABIC = re.compile(r"[؀-ۿ]")
_OCR_RUN = re.compile(r"[oae><|~^`\\]{4,}")           # runs of OCR junk symbols
_TATWEEL = "ـ"


def arabic_ratio(text: str) -> float:
    """Fraction of letters that are Arabic — used to detect language when the
    document has no `Language:` metadata (e.g. the OCR'd orientation guide)."""
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    return sum(1 for c in letters if _ARABIC.match(c)) / len(letters)


def _ocr_letter_ratio(line: str) -> float:
    s = line.strip()
    if not s:
        return 1.0
    letters = sum(1 for c in s if c.isalpha() or _ARABIC.match(c))
    return letters / len(s)


def clean_arabic(body: str) -> str:
    body = base_clean(body)
    body = body.replace(_TATWEEL, "")
    body = body.replace("**", "")                      # OCR wraps every word in bold
    # collapse the dotted/underscore "fill-in" runs found in form templates
    body = re.sub(r"[.…]{3,}", " ", body)
    body = re.sub(r"_{2,}", " ", body)

    out = []
    for line in body.split("\n"):
        s = line.strip()
        if _is_protected(line):
            out.append(line)
            continue
        if not s:
            out.append(line)
            continue
        if _OCR_RUN.search(s):
            continue
        if re.fullmatch(r"[-*•·.\s|=+)(]*", s):        # punctuation-only
            continue
        if re.fullmatch(r"\d+", s):                    # lone page/section number
            continue
        if len(s) >= 4 and _ocr_letter_ratio(s) < 0.4:  # mostly symbols -> junk
            continue
        out.append(line)
    return _collapse_blanks("\n".join(out))


# --------------------------------------------------------------------------- #
# Generic fallback
# --------------------------------------------------------------------------- #

def clean_generic(body: str) -> str:
    body = base_clean(body)
    out = []
    for line in body.split("\n"):
        if _is_protected(line) or line.strip():
            out.append(line)
        elif out and out[-1].strip():
            out.append(line)
    return _collapse_blanks("\n".join(out))
