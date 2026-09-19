# FSB Nexus — Project Status & Next Steps

> A living summary of **what's done** and **what's next**.
> For the detailed execution plan see [`PROJECT_COMPLETION_PLAN.md`](./PROJECT_COMPLETION_PLAN.md).
> Last updated: 2026-07-10.

---

## ✅ What we've done so far (Sprint 1 — complete)

All four Sprint-1 components are built and merged into `main` (PRs #10–#17).

### Backend (FastAPI + PostgreSQL/pgvector)
- JWT auth: register / login / email-verify, bcrypt password hashing, route guard middleware.
- Profile APIs (`GET/PATCH /profile`, onboarding status, academic-year).
- Chat APIs (`POST /chat`, sessions, messages) with per-owner scoping (IDOR fix).
- Documents APIs (`GET /documents`, admin `POST`).
- 11-table schema (students, courses, documents, document_chunks, chat_*, etc.).

### AI / RAG (Mistral + provider-agnostic client)
- 4 agents (Orientation, Academic, Administrative, Learning) with strict French prompts.
- Full pipeline: retrieve → retrieval grader → generate → citation formatter → groundedness grader.
- Provider abstraction (Mistral default, Gemini fallback; cheap judge model for grounding).
- Backend↔AI bridge via `RAG_PIPELINE_HANDLER=ai.integration:answer_chat`.
- Unit tests for prompts, citations, graders, pipeline.

### Knowledge Base
- ~85 cleaned FSB documents; structure-aware chunking pipeline.
- **3675 chunks ingested** into `document_chunks` (multilingual mpnet, 768-dim).
- Semantic search over pgvector (cosine similarity).

### Frontend (Next.js + Tailwind + shadcn)
- Auth pages (login/register/verify), dashboard, chat UI, profile.
- Dark/light theme, animations (Framer Motion), citation chips.

### Integration
- Full stack runs locally end-to-end (see [`RUNNING_LOCALLY.md`](../RUNNING_LOCALLY.md)):
  register → login → chat with real cited Mistral answers.

---

## 🔎 What we diagnosed (why it's not "done")

Investigation this week (traced through the live pipeline + DB) found:

1. **The chat over-refuses.** Not a bug in the pipeline — it does exactly what a safe
   RAG should. Root causes:
   - Agent prompts allow **only** grounded answers → greetings / small talk / general
     questions have **no path** and get refused.
   - **No conversation memory**: `session_id` is never passed into the pipeline.
   - **KB data quality**: answers exist but are buried in noisy scraped text
     (e.g. licence names lost among phone numbers), so pure-vector retrieval can't
     surface them — even at top-15.
2. **Frontend auth guard is disabled** (`(protected)/layout.tsx` — commented out).
3. **Security gaps**: no rate limiting, no password policy, JWT in localStorage,
   `CORS *`, silent exception-swallowing in `services/rag.py`, latent schema drift.
4. **Courses feature is absent** (table exists, unused); no Google Classroom.
5. **No streaming, no CI, no backend/frontend tests, unpinned deps.**

Full detail + security audit: [`PROJECT_COMPLETION_PLAN.md`](./PROJECT_COMPLETION_PLAN.md) §0–§1.

---

## 🎯 What's next (2-week MVP)

Committed scope for the next 2 weeks (4 people, outcome-based tracks):

- **Conversational Intelligence (A):** intent routing + conversational fallback +
  memory, hybrid retrieval + reranker, KB re-clean (top ~15 docs), eval harness.
  → *the chat stops refusing and answers faculty + document + general questions.*
- **Courses (B):** manual course add + material upload, scoped course→RAG ingestion,
  "ask about this course". *(Google Classroom OAuth = stretch, gated on Google/school approval.)*
- **Design & Frontend (C):** re-enable auth guard, streaming chat UI, citations
  viewer, conversation history, real dashboard, design polish.
- **Backend, Security & Platform (D):** fix High-severity security items, streaming
  (SSE) endpoint, history + feedback endpoints, documents→ingestion, admin bootstrap.

**MVP Definition of Done:** secure guarded auth · chat that streams, remembers, and
answers (eval answer-rate up sharply, groundedness ~100%) · manual courses answerable
in chat · polished, placeholder-free UI.

**Stretch (Sprint 3):** verified Google Classroom OAuth · CI/CD + Docker + Alembic ·
refresh tokens · password reset · real email verification · full i18n/a11y.

---

## 📌 Immediate next actions
- [ ] Team agrees the track split (it's **not** equal weight — see plan §2; pair on OAuth).
- [ ] Lock the shared API contracts (plan §3) so everyone works in parallel.
- [ ] Person D scaffolds streaming + feedback + courses stubs (mocks) on Day 1.
- [ ] Person A builds the **eval baseline** first — it's the scoreboard everyone gates on.
- [ ] Decide: turn the MVP tier into 4 GitHub issues (like the Sprint-1 set)?
