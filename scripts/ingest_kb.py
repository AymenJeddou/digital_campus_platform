"""Ingest the knowledge base into PostgreSQL + pgvector.

Reads ``knowledge_base/build/chunks.jsonl`` (produced by the KB chunking
pipeline), embeds each chunk with the multilingual model, and stores it in the
``document_chunks`` table so ``src.search.retriever.retrieve`` can serve it.

Self-contained (raw SQL, no backend import). Idempotent: re-running replaces the
existing rows. Run before starting the backend so the tables are created with
the correct ``vector(768)`` column type.

Usage:
    python scripts/ingest_kb.py
"""

from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ai.rag.db import get_session          # noqa: E402
from ai.rag.embeddings import embed_texts  # noqa: E402

CHUNKS_FILE = ROOT / "knowledge_base" / "build" / "chunks.jsonl"
BATCH_SIZE = 64
# Fixed namespace so chunk_id / document_id are deterministic across re-runs.
NS = uuid.UUID("9b1d2c3e-0000-4a00-8a00-abcdef010001")

DDL = [
    "CREATE EXTENSION IF NOT EXISTS vector",
    """CREATE TABLE IF NOT EXISTS documents (
        id UUID PRIMARY KEY,
        title TEXT,
        content TEXT,
        uploaded_at TIMESTAMP DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS document_chunks (
        chunk_id UUID PRIMARY KEY,
        document_id UUID REFERENCES documents(id),
        text TEXT,
        title TEXT,
        source TEXT,
        page INTEGER,
        category TEXT,
        embedding vector(768)
    )""",
]


def main() -> None:
    if not CHUNKS_FILE.exists():
        sys.exit(f"Chunks file not found: {CHUNKS_FILE}")

    rows = [
        json.loads(line)
        for line in CHUNKS_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    print(f"Loaded {len(rows)} chunks from {CHUNKS_FILE.name}")

    db = get_session()
    try:
        for stmt in DDL:
            db.execute(text(stmt))
        db.commit()

        # Fresh ingest.
        db.execute(text("DELETE FROM document_chunks"))
        db.execute(text("DELETE FROM documents"))
        db.commit()

        # One documents row per distinct source.
        sources = {}
        for r in rows:
            sources.setdefault(r["source"], r.get("title") or r["source"])
        src_to_doc = {}
        for source, title in sources.items():
            doc_id = uuid.uuid5(NS, "doc:" + source)
            src_to_doc[source] = str(doc_id)
            db.execute(
                text("INSERT INTO documents (id, title, content) VALUES (:id, :t, '')"),
                {"id": str(doc_id), "t": title},
            )
        db.commit()
        print(f"Created {len(sources)} document rows")

        # Embed + insert chunks in batches.
        insert = text("""
            INSERT INTO document_chunks
                (chunk_id, document_id, text, title, source, page, category, embedding)
            VALUES
                (:cid, :did, :txt, :ttl, :src, :pg, :cat, CAST(:emb AS vector))
        """)
        total = 0
        for i in range(0, len(rows), BATCH_SIZE):
            part = rows[i:i + BATCH_SIZE]
            vectors = embed_texts([r["text"] for r in part], show_progress=False)
            for r, vec in zip(part, vectors):
                db.execute(insert, {
                    "cid": str(uuid.uuid5(NS, r["chunk_id"])),
                    "did": src_to_doc[r["source"]],
                    "txt": r["text"],
                    "ttl": r.get("title") or r["source"],
                    "src": r["source"],
                    "pg": r.get("page") or 0,
                    "cat": r.get("category") or "general",
                    "emb": str(vec),
                })
            db.commit()
            total += len(part)
            print(f"  embedded + stored {total}/{len(rows)}")

        # Approximate-NN index for cosine distance.
        db.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON document_chunks "
            "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
        ))
        db.commit()
        print(f"DONE: {total} chunks ingested into document_chunks.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
