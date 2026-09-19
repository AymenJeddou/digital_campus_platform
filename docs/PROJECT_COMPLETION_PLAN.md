# FSB Nexus — Project Completion Plan (2 Weeks, 4 People)

> Goal: ship a **working, professional** AI campus assistant in 2 weeks.
> By the end: secure login → onboarding → a chat that answers **anything** about the
> faculty, the documents, **your own courses (via Google Classroom)**, and holds a
> normal conversation — wrapped in a design that looks impressive and polished.
>
> This plan is based on a full read of the current codebase (backend, frontend,
> `ai/`, `knowledge_base/`). It **replaces** the old sprint roles and the blueprint.

---

## ⚠️ Reality check — read this first

**Everything below is more than 2 weeks of work for 4 part-time students.** The full
scope (security overhaul + Google OAuth + streaming + memory + hybrid retrieval +
reranker + KB re-clean + real dashboard + onboarding + design pass + i18n/a11y +
email verify + password reset + refresh tokens + CI/CD + Docker + migrations) is
realistically 6–10 person-weeks. So this plan is split into two tiers:

- **🎯 MVP (commit to this in 2 weeks)** — a genuinely working, good-looking,
  demo-able app.
- **🌟 Stretch (Sprint 3 / only if ahead)** — the production-hardening and the
  parts that depend on external approvals.

**MVP scope (the promise):**
- Chat **stops over-refusing**: intent routing + conversational fallback + memory,
  hybrid retrieval + reranker, KB re-clean of the top ~15 docs.
- **Re-enable the frontend auth guard** + top-5 security fixes (§1 High).
- **Streaming chat UI** + citations viewer + conversation history.
- **Courses via manual upload/entry** (see the Google note below), surfaced in chat.
- **Design polish** on the pages that already exist (no placeholders).

**Stretch (explicitly deferred):** verified Google Classroom OAuth, CI/CD, Alembic
migrations, password reset, refresh tokens, full i18n/a11y, real email verification.

> **On Google Classroom:** Google's OAuth verification for sensitive Classroom
> scopes takes days-to-weeks, unverified apps are capped/warning-walled, and the
> school's Google Workspace may block third-party access entirely. **Make manual
> course upload the primary 2-week path; treat live verified Classroom OAuth as the
> stretch goal.** Build the manual path first so this requirement can't sink the sprint.

---

## 0. Where we are today (honest state of the code)

**What works**
- End-to-end auth (register/login/JWT), profile, chat, documents endpoints exist.
- RAG pipeline works: retrieve → grade → generate (Mistral) → cite → groundedness.
- 3675 KB chunks ingested in Postgres+pgvector; semantic search returns results.
- Next.js frontend with dark/light theme, animations, auth/chat/dashboard pages.

**What's broken or missing (the real backlog)**
| Area | Problem found in code |
|---|---|
| **Chat over-refuses** | Agent prompts force *"answer ONLY from context, else refuse"* — no path for greetings, small talk, or general questions. Pure-vector retrieval on noisy chunks misses answers that exist. |
| **No conversation memory** | `session_id` is never passed into `RAGPipeline.run()`; the LLM sees one message at a time. No follow-ups, no "basic conversation". |
| **KB data quality** | Scraped docs are run-on blobs / bare noisy lists (e.g. `dep_mathematiques` buries "Licence Fondamentale de Mathématiques" among phone numbers). Answers exist but are un-retrievable. |
| **No courses feature** | `courses` table exists but is empty and unused. No Google Classroom integration anywhere. |
| **Frontend auth disabled** | `(protected)/layout.tsx` has the token guard **commented out** — protected pages are open to anyone. |
| **Security gaps** | See §1. localStorage tokens, no rate limiting, no password policy, `CORS *`, schema drift, silent exception-swallowing. |
| **No streaming** | Chat is a single synchronous POST; UI can't stream tokens. |
| **Placeholders** | Dashboard cards, "JD" avatar, recommendations are hardcoded. Document upload stores a row but never ingests. |
| **No CI / no backend & frontend tests** | `.github/` is empty; only `ai/` has tests. Dependencies mostly unpinned. |

---

## 1. Security audit (fix these — grouped by severity)

### 🔴 High
1. **Frontend route guard disabled** — `frontend/src/app/(protected)/layout.tsx:24-32`. The `localStorage` token check is commented out. Re-enable it and redirect to `/login` when absent/expired.
2. **No rate limiting on `/auth/login`** — brute-force / credential-stuffing open. Add `slowapi` (e.g. 5/min/IP on login+register).
3. **No password policy** — `schemas/auth.py` should enforce min length (≥8), and reject trivial passwords. Currently anything is accepted.
4. **Two sources of truth for `document_chunks`** — `scripts/ingest_kb.py` creates `embedding` as **`vector(768)`**, while `db.database.ensure_schema()` would add it as **JSONB** if it's missing. In the documented *ingest-first* flow this doesn't fire (the column already exists), so it's a **latent** risk, not an active bug — but if the backend ever starts before ingestion (and pgvector's `Vector` import isn't available), you get a JSONB column and broken similarity search. Fix by making ingest the single owner of that column (or move to Alembic migrations) so the drift can't happen.
5. **Silent exception swallowing** — `services/rag.py` catches *all* exceptions and returns `"RAG pipeline will be connected soon."` to the user. This hides real failures and leaks a dev placeholder. Log the error; return a proper error state.

### 🟠 Medium
6. **JWT in `localStorage`** (`lib/api.ts`, `lib/auth.ts`) — XSS-stealable. Move to httpOnly, `SameSite=Strict`, `Secure` cookies, or at minimum add a strict CSP and short token TTL + refresh tokens.
7. **`CORS allow_origins=["*"]`** (`main.py`) — lock to the known frontend origin(s) in production via env.
8. **Token lifecycle** — 30-min access token, **no refresh token**, no frontend expiry handling → abrupt logouts and silent 401s. Add refresh tokens + interceptor that refreshes/redirects on 401.
9. **Account enumeration** — `/register` returns "Email already registered"; `/login` returns distinct 401 vs 403 (not verified). Use generic messages.
10. **No admin bootstrap** — `role="admin"` can't be set via any API (profile blocks it), so `/documents` POST (admin-only) is unusable. Add a seed script / CLI to create the first admin.

### 🟡 Low / hardening
11. **Pin all dependencies** — `backend/requirements.txt` and `ai/requirements.txt` are mostly unpinned (already bit us with `bcrypt`). Pin exact versions; add `pip-audit`.
12. **Secrets hygiene** — confirm `.env` stays git-ignored (it is), `SECRET_KEY` is strong & unique per env, `AUTO_VERIFY_EMAIL=false` in prod. Add a `.env.example` completeness check.
13. **Audit logging** — `audit_logs` table exists but is never written. Log auth events + admin actions.
14. **Security headers** — add `X-Content-Type-Options`, `X-Frame-Options`/frame-ancestors, HSTS via middleware.

---

## 2. The 2-week plan — 4 tracks (no legacy roles)

I split by **outcome**, not by old component, so each person owns one end-to-end
result and can demo it independently. Names are placeholders — assign by interest.

> Interfaces between tracks are defined in §3 so people can work in parallel
> against contracts instead of waiting on each other.

**Honest load distribution (read before assigning):** the four tracks are **not
equal in weight or difficulty.**
- **Person D (backend/security/platform)** and **Person A (AI brain)** carry the
  most — they're the deepest and are on the critical path.
- **Person B (Google Classroom full-stack)** is the **hardest slice to assign**:
  OAuth backend + API + scoped ingestion + UI is a lot for one person and maps to
  none of the team's existing strengths. **It should be a pair (B + D on OAuth), or
  descoped to manual-upload for MVP** so it fits one person.
- **Person C (design/frontend)** is broad but well-bounded; give C backend help for
  the dashboard's real data.
Balance it by pairing on the two-sided work (OAuth, the feedback flywheel) and by
having whoever finishes first help A with the KB re-clean (the tedious critical-path
item). **Don't hand these down — agree them as a team.**

### 👤 Person A — Conversational Intelligence (AI/RAG + data quality)
**Outcome:** the chat answers **anything** — faculty facts, document questions, *and*
normal conversation — and stops over-refusing, without hallucinating.

- **Conversation layer**: pass session history into the pipeline; add short-term
  memory (last N turns) so follow-ups work.
- **Intent routing / conversational fallback**: before RAG, classify the message
  (greeting / smalltalk / meta "what can you do" / factual). Only factual questions
  hit the strict grounded path; greetings & meta get a friendly, bounded reply
  (no citations, no hallucinated facts). This is the single biggest fix for
  "it refuses everything".
- **Retrieval upgrade**: hybrid search (BM25 + vector + Reciprocal Rank Fusion) +
  a cross-encoder **reranker**. Fixes un-retrievable answers.
- **Refusal tuning**: soften the "refuse unless perfect context" rule to
  "answer from context; if partially relevant, answer what's supported and say
  what isn't" — keep groundedness gate for factual claims only.
- **KB re-clean (top ~15 docs)**: department pages, `fsb_licences`, `fsb_masteres`,
  `fsb_presentation`; strip contact-noise, split professor tables out, re-OCR
  `guide2025`. (Pair with Person B for course docs.)
- **Eval harness (RAG Triad)**: 25+ real Q/A, measure answer-rate + groundedness
  before/after every change. This is the shared scoreboard everyone's DoD gates on.

### 👤 Person B — Courses & Google Classroom (full-stack vertical)
**Outcome:** a student adds their courses (manual first, Google Classroom if
approved), sees them in-app, and the chat can answer questions about **their** course
content.

> **Build order matters:** do **manual course entry + file upload FIRST** (it's the
> MVP path and can't be blocked), then layer Google Classroom on top as stretch.
> Pair with Person D on the OAuth backend — it's genuinely two-sided.

- **MVP — manual courses**: add course + upload materials (PDF/docx) UI + endpoints;
  persist to `courses` (+ new `course_materials`) tables.
- **MVP — Course → RAG ingestion**: chunk & embed the student's course materials into
  a **per-student, scoped** namespace so "explique le TP de la semaine 3" works.
  (Reuse Person A's ingestion + retriever; add `student_id`/`course_id` scoping.)
- **MVP — Course endpoints**: `GET /courses`, `GET /courses/{id}`, `POST /courses`.
- **MVP — Course UI** (with Person C): a Courses page — list, detail, materials,
  "ask about this course" deep-link into chat.
- **🌟 Stretch — Google Classroom**: OAuth2 "Connect Classroom" (consent → tokens
  stored encrypted per student; scopes `courses.readonly`, `coursework.readonly`,
  `announcements.readonly`), then `POST /courses/sync` to import courses/coursework/
  materials. Gated on Google app verification + the school Workspace allowing it.

### 👤 Person C — Design & Frontend Experience
**Outcome:** the app looks professional, impressive, and cohesive; every feature is
wired to real data (no placeholders).

- **Re-enable + finish auth guard** (the disabled one), real user avatar/name from
  `/profile`, working logout, 401→login redirect.
- **Streaming chat UI**: token-by-token rendering (wire to Person D's SSE),
  typing indicators, error/retry states, markdown rendering (safe — no
  `dangerouslySetInnerHTML`).
- **Citations UX**: citation chips → clickable source viewer (document + page).
- **Conversation history sidebar**: list/resume/rename/delete sessions.
- **Onboarding flow**: status / academic year / bac info / interests → drives agent
  routing and personalization.
- **Real dashboard**: recommendations, quick actions, "your courses" summary
  (from Person B), recent chats.
- **Design system pass**: consistent tokens, spacing, motion; responsive; dark/light;
  French i18n; accessibility (focus states, aria, contrast). Make it *feel* premium.

### 👤 Person D — Backend, Security & Platform
**Outcome:** the API is robust, secure, and exposes everything A/B/C need; the app
is deployable.

- **Fix all §1 security items** (guard is C's UI, but rate-limit, password policy,
  CORS lockdown, schema-drift, error handling, enumeration, admin bootstrap,
  dependency pinning, headers are here).
- **Streaming endpoint** (SSE) for chat so C can stream and A can push tokens.
- **Conversation history + feedback**: `GET /chat/sessions`, messages persistence
  with citations, `POST /chat/feedback` (👍/👎) feeding A's eval set.
- **Documents → ingestion pipeline**: admin upload actually triggers chunk+embed.
- **Google OAuth backend plumbing** with Person B (token storage/encryption,
  refresh, callback route).
- **Real email verification + password reset** (replace `AUTO_VERIFY_EMAIL` dev
  shortcut) — SMTP configured.
- **CI/CD**: GitHub Actions (lint + tests for backend/frontend/ai + `pip-audit`),
  Dockerize, one-command deploy (Compose), migrations (Alembic) to kill the
  `ensure_schema()` hack.

---

## 3. Shared contracts (so tracks don't block each other)

Agree these **on day 1**; then everyone codes against the interface.

**Chat (streaming) — D → A, C**
```
POST /chat/stream   (SSE)
body: { message: string, session_id?: uuid }
events: token {delta}  → ... → done { session_id, citations: [{document, page}] }
```

**Chat feedback — C → D → A**
```
POST /chat/feedback  { message_id: uuid, rating: "up" | "down", note?: string }
```

**Courses — B → C**
```
POST /courses/sync            → { synced: n }
GET  /courses                 → [{ id, name, source: "classroom"|"manual", updated_at }]
GET  /courses/{id}            → { id, name, materials: [...], announcements: [...] }
```

**Pipeline call (memory + scope) — A internal, used by D**
```
answer_chat(message, session_id, student, history=[...], course_scope?=course_id)
  → { answer, citations, intent }
```

**The quality flywheel**: `C feedback UI → D endpoint → A eval set → shows which
docs to fix → A/B clean them → retrieval improves.` Wire it early.

---

## 4. Two-week timeline

### Week 1 — foundations & unblock
- **Day 1**: kickoff. Lock the §3 contracts. D scaffolds streaming + feedback +
  courses route stubs (returning mocks) so A/B/C can build immediately. A builds
  the eval baseline (the scoreboard) and starts intent routing. C re-enables auth
  guard + wires real profile. B starts Google OAuth.
- **Days 2-3**: A: conversational fallback + memory. B: Classroom sync + course
  models. C: streaming chat UI against D's SSE mock, history sidebar. D: security
  fixes (rate limit, password policy, CORS, schema drift, error handling).
- **Days 4-5**: A: hybrid retrieval + reranker, first KB re-clean. B: course →
  RAG ingestion (scoped). C: citations viewer + real dashboard. D: real streaming +
  feedback + documents ingestion + CI green.
- **End of Week 1 demo**: login (guarded) → ask a factual question → grounded cited
  streamed answer; say "bonjour" → friendly reply (no refusal); link Classroom →
  courses appear.

### Week 2 — completion & polish
- **Days 6-7**: A: refusal tuning + finish KB top-15, eval shows big answer-rate
  gain. B: "ask about this course" end-to-end. C: onboarding flow + design system
  pass. D: email verify + password reset + admin bootstrap + deploy pipeline.
- **Days 8-9**: integration hardening — full flow across all tracks; fix cross-track
  bugs; accessibility + responsive + i18n; security re-review (§1 all closed).
- **Day 10**: freeze, final eval run, deploy, demo rehearsal, README/docs.

---

## 5. Definition of Done

**🎯 MVP (2-week commitment):**
- [ ] Auth: frontend guard re-enabled, rate-limited login, password policy, all §1
      **High** items closed.
- [ ] Chat: streams; answers faculty + document questions with correct citations;
      handles greetings/small talk/meta gracefully; multi-turn memory; **eval
      answer-rate up sharply with groundedness ~100%** (no new hallucinations).
- [ ] Courses: **manual** course add + material upload; chat answers questions about
      the student's own courses.
- [ ] Design: professional, cohesive, responsive, dark/light; existing pages have
      **no placeholders** — everything wired to real data.

**🌟 Stretch (Sprint 3 / if ahead):**
- [ ] Verified Google Classroom OAuth sync.
- [ ] §1 Medium/Low closed: refresh tokens, real email verify + password reset,
      CORS lockdown, enumeration, audit logging, security headers.
- [ ] Platform: CI green (backend+frontend+ai tests + pip-audit), Dockerized,
      one-command deploy, Alembic migrations (retire the `ensure_schema` hack).
- [ ] Full i18n (FR/EN) + accessibility pass.

---

## 6. Risks & mitigations
- **Google Classroom API restricted by the school Workspace** → build the manual
  course upload fallback first so Person B is never fully blocked.
- **KB re-clean is tedious and on the critical path** → time-box to the top ~15
  docs that cover the most-asked questions; measure with the eval set, stop when
  answer-rate is good enough. Pair A with whoever finishes early.
- **Scope creep in 2 weeks** → anything not in §5 DoD is explicitly Sprint-3
  backlog (advanced recommendations, analytics, multi-language beyond FR/EN,
  mobile app).
- **Cross-track coupling** → §3 contracts + D's day-1 mocks decouple everyone.

---

## 7. My opinion (candid summary)
- **Scope is the #1 risk, not effort.** The team cannot finish *everything* in 2
  weeks — commit to the **MVP tier (§0.5)** and treat the rest as Sprint 3. A plan
  that promises the stretch scope in 2 weeks will miss the deadline.
- The split is by **outcome**, so it demos well per person — but it's **not equal
  weight** (see the load-distribution note in §2). Fix that by pairing on OAuth and
  the flywheel, and by helping A with the KB re-clean.
- **The critical path is A's retrieval/data + D's streaming contract.** Land the §3
  contracts and D's day-1 mocks or the parallelism collapses.
- **Google Classroom is the biggest external unknown** — manual-first protects the
  deadline; live OAuth is a bonus, not a promise.
- **Discuss and adjust as a team** — ownership should be chosen, not assigned.
