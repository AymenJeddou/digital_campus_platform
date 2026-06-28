"""
Structure-aware chunker.

Goal: chunks that preserve meaning and are good for retrieval, rather than blind
fixed-size windows that cut sentences and tables in half.

Strategy
--------
1. Walk the cleaned markdown, tracking:
     - current page    (updated by `[p.N]` markers; falls back to section index)
     - current section (the nearest markdown heading)
2. Group content into "units" = paragraphs, headings, or whole tables.
3. Pack units belonging to the *same section* into chunks up to a soft token
   target, never exceeding a hard cap (kept under the embedding model's limit).
4. Keep tables atomic; if one table alone is too big, split it on row
   boundaries (never mid-row) and repeat the header row on each piece.
5. Add a small token overlap between consecutive chunks of the same section so
   context isn't lost at the seam.
6. Prepend the section heading to each chunk's text — a cheap, high-value
   context boost for embeddings ("contextual chunk").

Output records match the FSBridge V2 schema (minus `embedding`/`score`, which
are added later by embed.py and at query time):

    {chunk_id, text, title, source, page, category}

`chunk_id = md5(f"{source}::{section_idx}::{sub_idx}")[:12]` — stable across
re-runs, exactly as documented in the handoff.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

# Sizing. mpnet-multilingual handles 512 tokens; we stay well under for quality.
TARGET_TOKENS = 350      # soft target — stop adding units past this
MAX_TOKENS = 480         # hard cap — never exceed
OVERLAP_TOKENS = 60      # carried from the tail of the previous chunk
MIN_TOKENS = 18          # drop/merge slivers smaller than this

_PAGE_MARKER = re.compile(r"\[p\.(\d+)\]")
_HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(?P<text>.*)$")
_WORDISH = re.compile(r"\w+|[^\w\s]", re.UNICODE)


def est_tokens(text: str) -> int:
    """
    Dependency-free token estimate. Counts word-ish + punctuation pieces and
    applies a 1.3x sub-word factor. Conservative enough that the hard cap keeps
    every chunk safely inside the model's real token limit, so we avoid pulling
    in a heavyweight tokenizer at the cleaning stage.
    """
    return int(len(_WORDISH.findall(text)) * 1.3)


@dataclass
class Unit:
    text: str
    page: int
    section: str        # heading text (or "" before the first heading)
    section_idx: int    # 0-based index of the section in the document
    is_table: bool = False


# --------------------------------------------------------------------------- #
# 1-2) markdown -> units
# --------------------------------------------------------------------------- #

def _is_table_row(line: str) -> bool:
    return line.count("|") >= 2


def split_units(body: str) -> list[Unit]:
    units: list[Unit] = []
    page = 0
    section = ""
    section_idx = -1            # becomes 0 at first heading; -1 = pre-heading
    para: list[str] = []
    table: list[str] = []

    def flush_para():
        nonlocal para
        if para:
            text = "\n".join(para).strip()
            if text:
                units.append(Unit(text, max(page, 0), section, max(section_idx, 0)))
            para = []

    def flush_table():
        nonlocal table
        if table:
            text = "\n".join(table).strip()
            if text:
                units.append(Unit(text, max(page, 0), section, max(section_idx, 0), is_table=True))
            table = []

    for raw in body.split("\n"):
        line = raw.rstrip()

        pm = _PAGE_MARKER.search(line)
        if pm and not line.strip().replace(pm.group(0), "").strip():
            # a standalone page marker line: update page, don't emit it
            flush_para(); flush_table()
            page = int(pm.group(1))
            continue

        hm = _HEADING.match(line)
        if hm:
            flush_para(); flush_table()
            section = hm.group("text").strip()
            section_idx += 1
            continue

        if _is_table_row(line):
            flush_para()
            table.append(line)
            continue
        else:
            flush_table()

        if line.strip() == "":
            flush_para()
        else:
            para.append(line)

    flush_para(); flush_table()
    return units


# --------------------------------------------------------------------------- #
# 4) oversized table -> row-boundary pieces with repeated header
# --------------------------------------------------------------------------- #

def _split_table(unit: Unit) -> list[str]:
    rows = unit.text.split("\n")
    header = rows[0] if rows else ""
    pieces: list[str] = []
    current: list[str] = []

    def emit():
        if current:
            pieces.append("\n".join(current))

    for idx, row in enumerate(rows):
        candidate = current + [row]
        if current and est_tokens("\n".join(candidate)) > MAX_TOKENS:
            emit()
            # restart with the header repeated for context (unless this row is it)
            current = [header] if header and idx != 0 else []
            current.append(row)
        else:
            current.append(row)
    emit()
    return pieces


# Separators tried in order when a single unit is too big to fit one chunk.
_SENTENCE = re.compile(r"(?<=[.!?؟।])\s+")


def _greedy_pack(parts: list[str], joiner: str) -> list[str]:
    """Greedily group already-small parts into pieces under TARGET_TOKENS."""
    pieces, cur = [], []
    for part in parts:
        if cur and est_tokens(joiner.join(cur + [part])) > TARGET_TOKENS:
            pieces.append(joiner.join(cur))
            cur = [part]
        else:
            cur.append(part)
    if cur:
        pieces.append(joiner.join(cur))
    return pieces


def _split_oversized_text(text: str) -> list[str]:
    """
    Split a non-table unit that exceeds the hard cap. Tries progressively finer
    boundaries — lines, then sentences, then words — so we never cut a chunk in
    the middle of a sentence unless a single sentence is itself too long.
    """
    if est_tokens(text) <= MAX_TOKENS:
        return [text]

    for parts, joiner in ((text.split("\n"), "\n"), (_SENTENCE.split(text), " ")):
        if len(parts) > 1:
            out: list[str] = []
            for piece in _greedy_pack([p for p in parts if p.strip()], joiner):
                out.extend(_split_oversized_text(piece) if est_tokens(piece) > MAX_TOKENS else [piece])
            return out

    # No line/sentence boundaries (e.g. OCR'd Arabic fragments): accumulate
    # whole words until the *estimated* token count hits the cap. Measuring with
    # est_tokens (not a word count) keeps Arabic, where one word ~ several
    # tokens, safely under the limit.
    out, cur = [], []
    for word in text.split():
        if cur and est_tokens(" ".join(cur + [word])) > MAX_TOKENS:
            out.append(" ".join(cur))
            cur = [word]
        else:
            cur.append(word)
    if cur:
        out.append(" ".join(cur))
    # Ultimate backstop for a single un-splittable token: slice on characters.
    final: list[str] = []
    for piece in out:
        if est_tokens(piece) > MAX_TOKENS:
            step = max(1, int(len(piece) * MAX_TOKENS / est_tokens(piece)))
            final.extend(piece[i:i + step] for i in range(0, len(piece), step))
        else:
            final.append(piece)
    return final or [text]


# --------------------------------------------------------------------------- #
# 3,5,6) pack units -> chunks
# --------------------------------------------------------------------------- #

def _tail_overlap(text: str) -> str:
    """Return the last ~OVERLAP_TOKENS worth of text (whole words)."""
    words = text.split()
    if not words:
        return ""
    keep = max(1, int(OVERLAP_TOKENS / 1.3))
    return " ".join(words[-keep:])


def _make_text(section: str, body: str) -> str:
    """Prepend the section heading for context, avoiding duplication."""
    section = section.strip()
    if section and not body.lstrip().startswith(section):
        return f"{section}\n{body}".strip()
    return body.strip()


def pack_units(units: list[Unit]) -> list[dict]:
    """Pack units into chunk dicts carrying section/page/text (no ids yet)."""
    chunks: list[dict] = []
    buf: list[str] = []
    buf_section = ""
    buf_section_idx = 0
    buf_page = 0
    overlap = ""

    def flush():
        nonlocal buf, overlap
        if not buf:
            return
        body = "\n\n".join(buf).strip()
        if est_tokens(body) >= MIN_TOKENS or not chunks:
            text = _make_text(buf_section, body)
            # Final guardrail: overlap + prepended heading can push a packed
            # chunk past the hard cap, so split here if needed.
            for piece in _split_oversized_text(text):
                chunks.append({
                    "section_idx": buf_section_idx,
                    "section": buf_section,
                    "page": buf_page,
                    "text": piece,
                })
            overlap = _tail_overlap(body)
        buf = []

    for unit in units:
        # section change -> start a fresh chunk (no overlap across sections)
        if unit.section_idx != buf_section_idx and buf:
            flush()
            overlap = ""

        # a unit that doesn't fit on its own gets split: tables on row
        # boundaries (header repeated), prose on sentence/line boundaries
        if est_tokens(unit.text) > MAX_TOKENS:
            flush(); overlap = ""
            pieces = _split_table(unit) if unit.is_table else _split_oversized_text(unit.text)
            for piece in pieces:
                chunks.append({
                    "section_idx": unit.section_idx,
                    "section": unit.section,
                    "page": unit.page,
                    "text": _make_text(unit.section, piece),
                })
            continue

        if not buf:
            buf_section = unit.section
            buf_section_idx = unit.section_idx
            buf_page = unit.page
            if overlap:
                buf.append(overlap)

        candidate = buf + [unit.text]
        if est_tokens("\n\n".join(candidate)) > TARGET_TOKENS and len(buf) > (1 if overlap else 0):
            flush()
            buf_section = unit.section
            buf_section_idx = unit.section_idx
            buf_page = unit.page
            if overlap:
                buf.append(overlap)
            buf.append(unit.text)
        else:
            buf.append(unit.text)

    flush()
    return chunks


# --------------------------------------------------------------------------- #
# public entry point
# --------------------------------------------------------------------------- #

def chunk_document(body: str, *, source: str, title: str, category: str) -> list[dict]:
    """Clean body -> list of schema-compliant chunk records."""
    units = split_units(body)
    packed = pack_units(units)

    records = []
    sub_counters: dict[int, int] = {}
    for c in packed:
        sec = c["section_idx"]
        sub = sub_counters.get(sec, 0)
        sub_counters[sec] = sub + 1
        key = f"{source}::{sec}::{sub}"
        records.append({
            "chunk_id": hashlib.md5(key.encode("utf-8")).hexdigest()[:12],
            "text": c["text"],
            "title": title,
            "source": source,
            "page": c["page"],
            "category": category,
        })
    return records
