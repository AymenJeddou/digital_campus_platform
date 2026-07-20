# FSB Nexus — Integration Plan

**Goal:** merge everyone's work into `develop` to reach an almost-ready application.
**Status:** planning only — nothing here has been merged or changed.

---

## 1. Current state — branches, PRs, and where they point

| Work | Branch | PR | Targets | Size | Owner |
|---|---|---|---|---|---|
| AI / RAG + Knowledge Base | `feature/kb-sprint2` | **#19** | `develop` ✓ | +14.7k / −66 | Aymen |
| Backend / Security / Platform (Role 4) | `amine-backend` | **#18** | `develop` ✓ | +527 / −316 | Amin |
| Courses & Integrations (Role 2) | `courses-and-integrations` | **#20** | `main` ✗ | +2388 / −5 | Abderrahim |
| Frontend (Role 3) | `better_front` | *none yet* | (based on `main`) | 7 files | — |

**Two structural problems before any feature work:**

1. **`main` is 1 commit ahead of `develop`** (the merge of PR #17 was never brought back into `develop`). `develop` is supposed to lead, not lag. Fix first: merge `main` → `develop` so `develop` ⊇ `main`, then treat `develop` as the single integration branch.
2. **PR #20 targets `main`; `better_front` is based on `main`.** Both must be retargeted to `develop`. Nothing should merge to `main` until `develop` is "almost ready", then `develop` → `main` once.

---

## 2. What each piece does RIGHT (keep)

**#19 — AI / RAG + KB (Aymen)**
- Evaluation harness (the shared scoreboard); measured, tested (43 pass).
- ivfflat full-recall fix + hybrid retrieval: hit@5 0.50 → 0.90.
- Intent routing, conversation memory, softened prompts: answer rate → 0.83, every answer cited.
- 29 atomic fact cards; 100-question hand-verified test.
- Isolated to `ai/` + `knowledge_base/` — **no backend-model conflict.**

**#20 — Courses & Integrations (Abderrahim)** — the strongest-engineered PR
- Full course model: `Course`, `StudentCourse`, `CourseMaterial`, enrollment endpoints.
- **Correct per-student chunk scoping**: adds `student_id` / `course_id` / `material_id` to `document_chunks`, with the rule *NULL = global KB chunk, set = course chunk visible only to that student*. This is the right design.
- Real material ingestion (chunk + embed) + text extraction (PDF/DOCX/PPTX).
- **Secure Google Classroom**: signed OAuth `state` (works with browser redirects), encrypted tokens (`token_crypto.py`), sync service. Has tests.

**#18 — Backend / Security (Amin)** — real hardening, keep most of it
- Token revocation + `/logout` blacklist, password policy, strict CORS, global error handlers.
- SSE streaming endpoint, feedback model + endpoint.
- `chat_messages.citations`, `documents.file_path` columns.

**`better_front` — Frontend**
- Reworked dashboard, sidebar, layout, global styles. Auth/chat/profile pages exist.

---

## 3. What's WRONG (must fix before merge)

### 3a. Two competing Google Classroom implementations — pick ONE
| | #18 | #20 |
|---|---|---|
| Token model | `GoogleClassroomToken` (**plaintext**) | `GoogleClassroomAccount` (**encrypted**) |
| Routes | `/google-classroom/*` | `/courses/classroom/*` |
| OAuth callback | **Broken** — depends on `get_current_user`, but Google redirects the browser with no auth header → always 401 | **Works** — signed `state` carries identity |
| Config vars | `GOOGLE_CLIENT_ID/SECRET/REDIRECT_URI` | `GOOGLE_CLASSROOM_CLIENT_ID/SECRET/...` + `GOOGLE_TOKEN_ENCRYPTION_KEY` |
| Sync / extraction / tests | none | yes |

**Decision: adopt #20's Google Classroom. Drop #18's** `google_classroom.py`, `GoogleClassroomToken`, and its Google config vars. Keep everything else in #18.

### 3b. #18 boot/security blockers (verified)
- **`fastapi_limiter` imported but not in `requirements.txt` and unused** → `ImportError` on startup. Delete the import.
- **No Redis server** (no `docker-compose` service, none running) → every login 500s. Add a redis service + `REDIS_URL`, or make the limiter fail-open.
- **Rate-limiter race**: `GET`-then-`INCR` isn't atomic; concurrent requests all pass. Use `INCR` first, then check.
- **Path traversal** in document upload: `f"{UPLOAD_DIR}/{file.filename}"` with attacker-controlled name. Use `os.path.basename` + generated name.
- **Feedback IDOR**: ownership check is commented out — any user can rate any message.
- **Document ingestion is a MOCK** (`sleeps 2s`, sets `is_ingested=True`, does not chunk/embed). The PR body claims otherwise. Replace with #20's real ingestion pattern, or wire to the KB ingest.

### 3c. Streaming bypasses the whole AI safety path (#18 ↔ #19)
`run_stream` is a parallel copy of the pipeline that skips **`grade_groundedness`**, **intent routing**, and **conversation memory**. `/chat/stream` is the path the frontend actually calls, so after a clean auto-merge it would have **zero hallucination protection** while the non-streaming path measures 0.00–0.09. **Rewire `run_stream` to reuse #19's `run()` path.**

### 3d. Frontend auth guard STILL disabled (`better_front`)
`(protected)/layout.tsx` still does `setIsAuthenticated(true)` unconditionally with the real check commented out. Any unauthenticated user reaches every protected page. **Re-enable the guard.** Also: JWT in `localStorage` (XSS-stealable) — acceptable for pilot, note as a follow-up.

---

## 4. What's MISSING (needed for "almost ready")

1. **Course-chunk scoping in retrieval (the #1 integration gap).** #20 adds the scoping *columns*, but #19's `semantic_search` retrieves **all** chunks with no filter. Merged as-is, course materials leak across students **and** pollute KB answers. `semantic_search` must gain: `WHERE student_id IS NULL OR (student_id = :sid AND course_id = :cid)`, and `answer_chat` must pass the student/course scope. This is the single most important glue task.
2. **Schema migration story.** No Alembic. `Base.metadata.create_all` does **not** `ALTER` existing tables, so new columns (`document_chunks` scoping, `chat_messages.citations`, `documents.file_path`) and new tables won't appear on an existing DB. Either add Alembic migrations, or accept `reset_db.py` + full re-ingest (loses the 3,706-chunk KB — must re-run `ingest_kb.py` after). Decide before deploy.
3. **Courses frontend.** `better_front` has no courses page — Role 2 has a backend and no UI. Needs: courses list, material upload, "ask about this course" link into chat.
4. **Streaming + feedback UI.** Frontend must consume `/chat/stream` (SSE) and expose the feedback endpoint.
5. **Single `.env.example`** covering every new setting: Redis, all Google vars, `GOOGLE_TOKEN_ENCRYPTION_KEY`, `FRONTEND_URL`.
6. **CI** running `pytest ai/tests` + `backend/tests` on PRs (both suites already exist).

---

## 5. Conflict matrix (files touched by more than one PR)

| File | #18 | #19 | #20 | Resolution |
|---|---|---|---|---|
| `backend/app/models/models.py` | RevokedToken, Feedback, GoogleClassroomToken | — | Course*, scoping cols, GoogleClassroomAccount | Use **#20 as base**; add #18's RevokedToken + Feedback; **drop** GoogleClassroomToken |
| `backend/app/core/config.py` | Google + FRONTEND_URL | — | Google Classroom + encryption + FRONTEND_URL | Keep #20's Google vars + one FRONTEND_URL; drop #18's Google vars |
| `backend/app/main.py` | google_classroom router, error handlers, CORS | — | courses router | Keep #20 courses + #18 error handlers/CORS; drop #18 google_classroom router |
| `backend/requirements.txt` | redis, sse-starlette, httpx | — | pypdf, python-docx, python-pptx, cryptography, PyJWT, requests | Union — no conflict |
| `ai/integration.py`, `ai/rag/pipeline.py` | run_stream | intent, memory, run() | — | **Auto-merges cleanly but semantically broken** — rewire run_stream through run() (§3c) |
| `backend/app/db/database.py` | reset_db.py (new) | — | ensure_schema edits | Keep both; reconcile with migration story (§4.2) |

---

## 6. Recommended merge order into `develop`

Order chosen to minimise conflict pain (independent first, then the two that both rewrite `models.py`, glue last).

1. **Reconcile base.** `git checkout develop && git merge main` (brings #17 in). Retarget PR #20 and (future) `better_front` PR to `develop`.
2. **Merge #19** (AI/KB). Isolated, tested, no backend-model conflict. Establishes the retrieval baseline everything else is measured against.
3. **Merge #20** (courses). Brings the canonical `models.py` (scoping + course models), real ingestion, and the good Google Classroom. Biggest foundational change.
4. **Merge #18** (backend security) **stripped of its Google Classroom**, with §3b blockers fixed. Resolve `models.py`/`config.py`/`main.py` conflicts per §5.
5. **Integration glue** (new small PR on `develop`):
   - Scope `semantic_search` on `student_id`/`course_id`; thread scope through `answer_chat` (§4.1).
   - Rewire `run_stream` through `run()` (§3c).
   - Migration or documented `reset_db` + re-ingest (§4.2).
   - Single `.env.example` (§4.5).
6. **Merge `better_front`** (open a PR to `develop`) with the auth guard re-enabled, plus courses / streaming / feedback UI (§3d, §4.3–4.4).
7. **CI** green on both test suites → `develop` → `main`.

---

## 7. Definition of "almost ready" (merge-done checklist)

- [ ] App boots: `uvicorn` starts, no ImportError, login works (Redis up).
- [ ] `develop ⊇ main`; #18/#19/#20 merged; `better_front` PR'd to `develop`.
- [ ] Auth guard enforced on the client; rate limiting, password policy, CORS, token revocation active.
- [ ] One Google Classroom implementation (#20's), tokens encrypted, OAuth callback works.
- [ ] Chat answers faculty questions with citations (eval harness green: hit@5 ≥ 0.9, answer rate ≥ 0.8, false-answer ≤ ~0.1).
- [ ] Streaming path routes through the grounded pipeline (grader + intent + memory), not the bypass copy.
- [ ] A student can add a course + upload material, and it's answerable **only for them** (scoping verified).
- [ ] Document ingestion is real, not the mock.
- [ ] `pytest ai/tests` + `backend/tests` pass in CI.
- [ ] One `.env.example` documents every setting.

---

## 8. Known follow-ups (post-pilot, not blockers)

- Course content (94% of KB corpus) is untested — build a course-content eval set.
- Remove the bad scholarship source (`bourses_etudiants_tunisie_montants_conditions` — a marketing article contradicting the official OOUN doc).
- Fact-card retrieval crowding: cap chunks per source in RRF, and/or raise `top_k`.
- JWT in `localStorage` → httpOnly cookie.
- False-answer rate is 0.00–0.09 (stochastic) — sample the eval over several runs in CI.
- Stale/mixed academic years in the corpus (2024-25 and 2025-26 coexist).
