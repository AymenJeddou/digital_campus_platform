# Knowledge-base cleaning & chunking pipeline

Turns the raw FSB documents into clean, schema-compliant chunks ready for
embedding. Stdlib only — no external dependencies.

```bash
cd knowledge_base
python -m pipeline.run            # clean + chunk everything -> build/
python -m pipeline.run --stats    # also print chunk token-size distribution
```

## What it does

```
raw .md  ──►  frontmatter.parse  ──►  cleaner (by type)  ──►  chunker  ──►  chunks.jsonl
             (title/lang/category)   (web/course/arabic/    (structure-     (+ clean mirror
                                       generic)               aware)           + manifest)
```

1. **`frontmatter.py`** — strips the `# Title` + `> **Key:** value` header (or the
   older `**Title:**/**Author:**` style) and returns metadata + body. Rejects
   OCR-garbage titles and falls back to the filename.
2. **`cleaners.py`** — one cleaner per data shape:
   - `clean_web` — HTML→markdown pages; drops nav/sidebar noise, image refs, and
     **professor name/grade rosters** (kept: dept head, formations, lab).
   - `clean_course` — program *maquettes*; re-flows exploded one-cell-per-line
     tables into readable pipe rows.
   - `clean_arabic` — OCR'd Arabic (orientation guide + admin forms); removes
     OCR junk runs, `**` noise, tatweel, and dotted fill-in lines.
   - `clean_generic` — fallback whitespace tidy-up.

   Language is taken from frontmatter, or **sniffed from content** when missing
   (the orientation guide has no header). All cleaners preserve `[p.N]` page
   markers and heading lines — the chunker needs them.
3. **`chunker.py`** — structure-aware chunking (see below).
4. **`run.py`** — routes every document, writes outputs under `build/`.

## Chunking strategy

The goal is *semantic preservation*, not fixed-size windows:

- Split on **headings** and **`[p.N]` page boundaries** into sections.
- Pack content into chunks up to a **soft target (~350 est. tokens)**, never past
  a **hard cap (~480)** — comfortably under the `paraphrase-multilingual-mpnet`
  512-token limit.
- **Tables stay atomic**; an oversized table is split on *row* boundaries with
  the header row repeated on each piece. Oversized prose is split on
  sentence/line boundaries, never mid-word unless unavoidable.
- A small **overlap (~60 tokens)** bridges consecutive chunks of the same
  section (never across sections).
- Each chunk is **prefixed with its section heading** for retrieval context.

`est_tokens()` is a dependency-free estimate (word-ish pieces × 1.3). It is
deliberately conservative so we don't need a heavyweight tokenizer here; the
real token budget is enforced again at embedding time.

## Output schema (`build/chunks.jsonl`)

Matches the FSBridge V2 contract. One JSON object per line:

| field | type | notes |
|---|---|---|
| `chunk_id` | str | `md5(f"{source}::{section_idx}::{sub_idx}")[:12]` — stable across re-runs |
| `text` | str | cleaned chunk, section heading prepended |
| `title` | str | human title from the document heading |
| `source` | str | cleaned filename, e.g. `guide2025_cleaned.md` |
| `page` | int | real `[p.N]` page when available, else 0-based section index |
| `category` | str | `orientation` \| `admissions` \| `course` \| `regulation` |

`embedding` (768-dim) and `score` are **not** produced here — they are added by
`embed.py` at ingestion and by `retrieve()` at query time.

## Known limitations

- **Maquette PDFs** (`course/pdf`, `course/docx`) explode every table cell onto
  its own line in the source. The cleaner re-flows them heuristically but does
  **not** reconstruct the exact grid — faithful reconstruction needs the
  original PDF layout and is error-prone. Numbers stay near their labels, which
  is enough for retrieval.
- A handful of chunks land a few estimated tokens over the cap (≤490). This is
  within the estimator's own margin and under the model limit.
- `professors/` is excluded from inputs (rosters dropped; dept descriptions are
  already covered by `orientation/web/dep_*`).
