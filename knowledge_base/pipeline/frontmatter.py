"""
Frontmatter parsing.

Documents in the knowledge base use two header styles:

  Style A (newer, harvested docs)
  ------------------------------------
  # Human Title
  > **Source:** http://...
  > **Category:** course
  > **Language:** fr
  > **Pages:** 4
  ---
  <body>

  Style B (older web dumps)
  ------------------------------------
  **Title:** ...
  **Author:** ...
  **Source:** [url](url)
  ---
  <body>

Some OCR documents (the Arabic orientation guide) have no real header at all,
just a garbage `#` line. This parser is deliberately tolerant: it returns a
`DocMeta` with whatever it could find and the body with the header stripped.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


# A "good" title has at least this fraction of alphanumeric characters.
# OCR garbage lines (e.g. "# o & \ i BERS Se a 7 ONE ZO") fail this test.
_MIN_TITLE_ALNUM_RATIO = 0.35

# `> **Key:** value`  or  `**Key:** value`
_META_LINE = re.compile(r"^>?\s*\*\*(?P<key>[^*]+?):\*\*\s*(?P<val>.*)$")
# A markdown link `[text](url)` -> we just want the url.
_LINK = re.compile(r"\[[^\]]*\]\((?P<url>[^)]+)\)")


@dataclass
class DocMeta:
    title: str | None = None
    source_url: str | None = None
    category: str | None = None
    language: str | None = None
    pages: int | None = None
    scope: str | None = None
    extra: dict[str, str] = field(default_factory=dict)


def _alnum_ratio(text: str) -> float:
    text = text.strip()
    if not text:
        return 0.0
    alnum = sum(1 for c in text if c.isalnum())
    return alnum / len(text)


def _looks_like_title(text: str) -> bool:
    """Reject OCR garbage: needs enough alnum density AND real words, not a
    soup of single characters like `o & \\ i BERS Se a 7 ONE ZO`."""
    if _alnum_ratio(text) < _MIN_TITLE_ALNUM_RATIO:
        return False
    tokens = text.split()
    if not tokens:
        return False
    one_char = sum(1 for t in tokens if len(t) == 1)
    return one_char / len(tokens) <= 0.3


def parse(raw_text: str) -> tuple[DocMeta, str]:
    """Return (DocMeta, body). The body has the header block removed."""
    meta = DocMeta()
    lines = raw_text.split("\n")

    # 1) Optional first-line title `# ...` (kept only if it is not OCR noise).
    cursor = 0
    if lines and lines[0].lstrip().startswith("#"):
        candidate = lines[0].lstrip("#").strip()
        if _looks_like_title(candidate):
            meta.title = candidate
        cursor = 1  # consume the line either way (garbage or used)

    # 2) Metadata lines + locate the `---` separator that ends the header.
    body_start = cursor
    for i in range(cursor, min(len(lines), cursor + 20)):
        line = lines[i].strip()
        if line == "---":
            body_start = i + 1
            break
        m = _META_LINE.match(line)
        if m:
            _assign_meta(meta, m.group("key").strip().lower(), m.group("val").strip())
            body_start = i + 1
        elif line == "" or line.startswith(">"):
            # blank or stray quote line inside the header region: skip it
            body_start = i + 1
        else:
            # first real content line -> header is over
            body_start = i
            break

    body = "\n".join(lines[body_start:]).strip()
    return meta, body


def _assign_meta(meta: DocMeta, key: str, value: str) -> None:
    if key == "source":
        link = _LINK.search(value)
        meta.source_url = link.group("url") if link else (value or None)
    elif key == "category":
        meta.category = value.lower() or None
    elif key == "language":
        meta.language = value.lower() or None
    elif key == "pages":
        digits = re.sub(r"[^0-9]", "", value)
        meta.pages = int(digits) if digits else None
    elif key == "scope":
        meta.scope = value or None
    elif key in ("title", "author", "retrieved"):
        if key == "title" and not meta.title and _looks_like_title(value):
            meta.title = value
        meta.extra[key] = value
    else:
        meta.extra[key] = value
