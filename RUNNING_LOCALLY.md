# Running FSB Nexus locally

This wires all four parts together so the full flow works on one machine:

```
Frontend (:3000) ──HTTP──> Backend (:8000) ──python──> AI pipeline ──> retriever ──> Postgres+pgvector ──> Mistral
```

## Prerequisites
- Docker (for Postgres + pgvector)
- Python 3.12+ and Node 18+
- A Mistral API key (https://console.mistral.ai/api-keys)

## 1. Database (Postgres + pgvector) and Redis
```bash
docker compose up -d          # starts Postgres (:5433) + Redis (:6379)
```
This uses `docker-compose.yml` at the repo root. Redis backs the `/auth/login`
rate limiter (without it the limiter fails open). Or start Postgres alone:
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
  `API_URL=http://localhost:8000`. Only the Next.js server calls the backend
  (the `/api/*` proxy keeps the login token in an httpOnly cookie).

## 4. Apply database migrations
Create the schema (and the `vector` extension) via Alembic. Run from `backend/`:
```bash
cd backend
alembic upgrade head
```
> Alembic is the only thing that creates or changes tables (the app never does).
> After changing a model: `alembic revision --autogenerate -m "..."`, review
> the file, then `alembic upgrade head`. The migrations also seed the FSB
> programme list used by onboarding.

## 5. Ingest the knowledge base (once)
Embeds the chunked KB into `document_chunks`.
```bash
python scripts/ingest_kb.py
```

## 6. Start the backend (:8000)
Run from `backend/` (so pydantic-settings finds `backend/.env`) with the repo
root on the path (so `ai` and `src` import):
```bash
cd backend
PYTHONPATH=.. uvicorn app.main:app --port 8000 --reload
```

## 7. Start the frontend (:3000)
```bash
cd frontend && npm install && npm run dev
```

## 8. Try it
Open http://localhost:3000 → Register → (auto-verified in dev) → Login → onboarding → Chat.
Switch to Arabic with the « العربية » button (the whole layout flips to RTL).

To see the admin dashboard, give your account the role in the database:
```bash
docker exec fsb-db psql -U postgres -d digital_campus -c "UPDATE students SET role='admin' WHERE email='you@example.com'"
```
Ask e.g. *"Quelles licences sont disponibles à la FSB ?"* and you should get a
grounded, cited French answer.

## How the pieces connect
- The browser only talks to the Next.js app. `/api/*` is a proxy
  (`frontend/src/app/api/[...path]/route.ts`) that forwards to `API_URL`,
  attaching the session token from an httpOnly cookie; SSE streams pass through.
- `/chat` (backend) imports the handler named by `RAG_PIPELINE_HANDLER`
  → `ai.integration.answer_chat` → `RAGPipeline(agent).run(...)`.
- The pipeline filters chunks (Day 5), generates with Mistral, formats citations
  (Day 4), and checks groundedness (Day 6).
- Chunks come from `src.search.retriever.retrieve` → `ai.rag.search.semantic_search`
  → pgvector similarity over `document_chunks`.

## Tests
```bash
python -m pytest ai/tests -q
# backend: needs Postgres; use a separate database
docker exec fsb-db psql -U postgres -c "CREATE DATABASE digital_campus_test"
cd backend && DATABASE_URL=postgresql://postgres:postgres@localhost:5433/digital_campus_test   sh -c "python -m alembic upgrade head && PYTHONPATH=.. python -m pytest tests -q"
cd frontend && npm run lint && npm run typecheck && npm run build
```

## Production notes
- Run uvicorn behind your reverse proxy with `--proxy-headers
  --forwarded-allow-ips=<proxy ip>` so rate limits see real client IPs.
- Set a unique `SECRET_KEY`, real SMTP settings, and `AUTO_VERIFY_EMAIL=false`.
- `scripts/reset_db.py` refuses non-local databases and asks for confirmation.

## Stopping
```bash
docker compose down          # database + redis
# Ctrl-C the backend and frontend terminals
```
