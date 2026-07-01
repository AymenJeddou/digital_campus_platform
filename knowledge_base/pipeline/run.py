"""
Knowledge-base cleaning + chunking pipeline (orchestrator).

Run from the knowledge_base/ directory:

    python -m pipeline.run            # clean + chunk everything
    python -m pipeline.run --stats    # also print per-category chunk stats

Inputs : the raw source documents under orientation/ admissions/ course/
         regulation/ (the `professors/` folder is intentionally excluded — its
         name/grade rosters were dropped per the agreed taxonomy, and the
         department descriptions already live under orientation/web/).

Outputs (all under build/):
    build/clean/<category>/<name>_cleaned.md   cleaned, human-readable mirror
    build/chunks.jsonl                         one JSON chunk per line
    build/manifest.json                        per-document stats + run summary

Chunk records follow the FSBridge V2 schema:
    {chunk_id, text, title, source, page, category}
`embedding` and `score` are added downstream (embed.py / retrieve()).
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from . import cleaners
from .chunker import chunk_document
from .frontmatter import parse

KB_ROOT = Path(__file__).resolve().parent.parent
BUILD = KB_ROOT / "build"

VALID_CATEGORIES = {"orientation", "admissions", "course", "regulation"}

# Folders fed into the pipeline, with the category each maps to and whether the
# content is "course-style" (table-heavy maquettes) so we can pick the cleaner.
# `professors/` is deliberately absent.
SOURCE_DIRS = [
    ("orientation/raw", "orientation"),
    ("orientation/web", "orientation"),
    ("admissions/national", "admissions"),
    ("admissions/web", "admissions"),
    ("course/pdf", "course"),
    ("course/docx", "course"),
    ("course/web", "course"),
    ("regulation/national", "regulation"),
    ("regulation/pdf", "regulation"),
    ("regulation/web", "regulation"),
]


def choose_cleaner(category: str, language: str | None, rel_dir: str, body: str):
    """Pick a cleaner from category + language + folder signals. Language is
    sniffed from content when metadata is missing (the OCR guide has no header)."""
    is_arabic = (language == "ar") or cleaners.arabic_ratio(body) > 0.2
    if is_arabic:
        return cleaners.clean_arabic, "arabic"
    if category == "course" and rel_dir.endswith(("pdf", "docx")):
        return cleaners.clean_course, "course"
    if rel_dir.endswith(("web", "national")):
        return cleaners.clean_web, "web"
    return cleaners.clean_generic, "generic"


def derive_category(meta_category: str | None, fallback: str) -> str:
    if meta_category in VALID_CATEGORIES:
        return meta_category
    return fallback


def process_file(path: Path, rel_dir: str, fallback_category: str) -> dict | None:
    raw = path.read_text(encoding="utf-8")
    meta, body = parse(raw)

    category = derive_category(meta.category, fallback_category)
    clean_fn, cleaner_name = choose_cleaner(category, meta.language, rel_dir, body)
    cleaned = clean_fn(body)

    if not cleaned.strip():
        return None  # nothing left after cleaning (e.g. an empty stub page)

    title = meta.title or path.stem
    source = f"{path.stem}_cleaned.md"

    # write the cleaned mirror
    out_dir = BUILD / "clean" / category
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / source).write_text(cleaned, encoding="utf-8")

    chunks = chunk_document(cleaned, source=source, title=title, category=category)

    return {
        "source": source,
        "title": title,
        "category": category,
        "language": meta.language,
        "cleaner": cleaner_name,
        "source_url": meta.source_url,
        "orig_path": str(path.relative_to(KB_ROOT)).replace("\\", "/"),
        "orig_chars": len(raw),
        "clean_chars": len(cleaned),
        "n_chunks": len(chunks),
        "chunks": chunks,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Clean + chunk the FSB knowledge base.")
    ap.add_argument("--stats", action="store_true", help="print per-category stats")
    args = ap.parse_args()

    BUILD.mkdir(exist_ok=True)
    docs: list[dict] = []
    skipped: list[str] = []

    for rel_dir, fallback_category in SOURCE_DIRS:
        src_dir = KB_ROOT / rel_dir
        if not src_dir.exists():
            continue
        for path in sorted(src_dir.glob("*.md")):
            result = process_file(path, rel_dir, fallback_category)
            if result is None:
                skipped.append(rel_dir + "/" + path.name)
            else:
                docs.append(result)

    # write chunks.jsonl
    all_chunks = [c for d in docs for c in d["chunks"]]
    with (BUILD / "chunks.jsonl").open("w", encoding="utf-8") as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    # write manifest.json (per-doc stats, no chunk bodies)
    manifest = {
        "summary": {
            "documents": len(docs),
            "skipped": skipped,
            "total_chunks": len(all_chunks),
            "chunks_by_category": dict(Counter(c["category"] for c in all_chunks)),
        },
        "documents": [{k: v for k, v in d.items() if k != "chunks"} for d in docs],
    }
    (BUILD / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # console report
    print(f"Documents processed : {len(docs)}")
    print(f"Documents skipped    : {len(skipped)}  {skipped if skipped else ''}")
    print(f"Total chunks         : {len(all_chunks)}")
    print(f"Chunks by category   : {manifest['summary']['chunks_by_category']}")
    print(f"Outputs              : {BUILD.relative_to(KB_ROOT)}/chunks.jsonl, manifest.json, clean/")

    if args.stats:
        from .chunker import est_tokens
        toks = [est_tokens(c["text"]) for c in all_chunks]
        toks.sort()
        n = len(toks)
        print("\nChunk token estimate (per chunk):")
        print(f"  min {toks[0]}  p50 {toks[n // 2]}  p90 {toks[int(n * 0.9)]}  max {toks[-1]}")
        empty = sum(1 for c in all_chunks if not c["text"].strip())
        print(f"  empty chunks: {empty}")


if __name__ == "__main__":
    main()
