# Running FSB Nexus locally

This wires all four parts together so the full flow works on one machine:

```
Frontend (:3000) ──HTTP──> Backend (:8000) ──python──> AI pipeline ──> retriever ──> Postgres+pgvector ──> Mistral
```

## Prerequisites
- Docker (for Postgres + pgvector)
- Python 3.12+ and Node 18+
- A Mistral API key (https://console.mistral.ai/api-keys)

## 1. Database (Postgres + pgvector)
```bash
docker run -d --name fsb-db \
  -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=digital_campus \
  -p 5433:5432 pgvector/pgvector:pg16
```
> Host port **5433** avoids clashing with a native Postgres on 5432. If 5432 is
> free on your machine, you may use it instead (update the URLs below).

## 2. Python environment (backend + AI in one venv)
```bash
python -m venv .venv && . .venv/Scripts/activate   # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt -r ai/requirements.txt
```
The AI deps include `torch` + `sentence-transformers` (the embedding model,
`paraphrase-multilingual-mpnet-base-v2`, downloads ~1 GB on first use).

## 3. Environment files
- `ai/.env` (copy from `ai/.env.example`): set `MISTRAL_API_KEY` and
  `DATABASE_URL=postgresql://postgres:postgres@localhost:5433/digital_campus`
- `backend/.env` (copy from `backend/.env.example`): set `DATABASE_URL` (same as
  above), a strong `SECRET_KEY`, `RAG_PIPELINE_HANDLER=ai.integration:answer_chat`,
  and `AUTO_VERIFY_EMAIL=true` (local only — lets you log in without SMTP).
- `frontend/.env.local` (copy from `frontend/.env.example`):
  `NEXT_PUBLIC_API_URL=http://localhost:8000`

## 4. Ingest the knowledge base (once)
Embeds the chunked KB into `document_chunks`. Run **before** the backend so the
table is created with the correct `vector(768)` type.
```bash
python scripts/ingest_kb.py
```

## 5. Start the backend (:8000)
Run from `backend/` (so pydantic-settings finds `backend/.env`) with the repo
root on the path (so `ai` and `src` import):
```bash
cd backend
PYTHONPATH=.. uvicorn app.main:app --port 8000 --reload
```

## 6. Start the frontend (:3000)
```bash
cd frontend && npm install && npm run dev
```

## 7. Try it
Open http://localhost:3000 → Register → (auto-verified in dev) → Login → Chat.
Ask e.g. *"Quelles licences sont disponibles à la FSB ?"* and you should get a
grounded, cited French answer.

## How the pieces connect
- The frontend calls `NEXT_PUBLIC_API_URL` for `/auth`, `/profile`, `/chat`.
- `/chat` (backend) imports the handler named by `RAG_PIPELINE_HANDLER`
  → `ai.integration.answer_chat` → `RAGPipeline(agent).run(...)`.
- The pipeline filters chunks (Day 5), generates with Mistral, formats citations
  (Day 4), and checks groundedness (Day 6).
- Chunks come from `src.search.retriever.retrieve` → `ai.rag.search.semantic_search`
  → pgvector similarity over `document_chunks`.

## Stopping
```bash
docker rm -f fsb-db          # database
# Ctrl-C the backend and frontend terminals
```
