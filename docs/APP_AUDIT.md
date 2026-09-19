guide_source.py# FSB Nexus — Full Application Audit

**Method:** manual end-to-end testing against the running stack (backend on `:8000`, frontend on `:3000`, Postgres+pgvector on `:5433`) plus source inspection. **No pytest** — every result below comes from real HTTP calls or reading the code. Real users were registered and driven through the actual flows.

**Verdict: a working, genuinely impressive RAG core wrapped in a demo-grade shell.** The retrieval, security and courses backend are real and correct. The dashboard is fake, there is no onboarding, and the flagship "ask about my course" feature only works about half the time. **Not production ready** — but the gap is mostly UI wiring and reliability, not architecture.

---

## 1. What actually works (verified live)

| Area | Evidence |
|---|---|
| **Registration + password policy** | `"weak"` → `400 Password must be at least 8 characters long`; strong → `201` |
| **Login / JWT** | `200` + token |
| **API access control** | `/profile`, `/chat/sessions`, `/courses/mine`, `/documents`, `/onboarding/status` all → **401** without a token |
| **Cross-user access (IDOR)** | Attacker reading victim's chat session → **404**; opening victim's course → **403**; adding material to it → **403** |
| **Logout / token revocation** | `/profile` `200` → logout `204` → `/profile` **401**. Blacklist works. |
| **CORS** | Locked to `FRONTEND_URL`, not `*` |
| **Chat answers for real** | *"Quelle est la licence en informatique ?"* → real answer, **3 citations** |
| **Refusal guardrail** | *"Quel est le salaire du doyen ?"* → correctly refuses, 0 citations |
| **Streaming (`/chat/stream`)** | Full SSE: `session_id` → **50 chunk events** → `grounded` → `citations` → `[DONE]`, 5.1s |
| **Courses backend** | create+enrol `201`; material `201` `status=ingested chunks=1`; `/courses/mine` `200` |
| **Course chunk scoping** | Scoped search returns the student's material at **rank 1, score 0.802**; unscoped correctly excludes it |
| **Profile page** | Genuinely fetches and edits real data (`academic_year`, `interests`, `goals`) |

The RAG core is the strongest part of this codebase: hybrid retrieval, citations, a groundedness guardrail, and per-student chunk isolation that actually holds.

---

## 2. Critical issues

### 2.1 "Ask about this course" only works ~50% of the time — the flagship feature
The same question, same course, same data, run four times:

```
run 1: citations=0  refused=True
run 2: citations=0  refused=True
run 3: citations=1  refused=False
run 4: citations=1  refused=False
```

Retrieval is **never** the problem — the material comes back at rank 1 (score 0.802), far above the 0.35 gate. The failure is downstream: the generator or the groundedness judge **non-deterministically refuses a valid, retrieved answer**.

This is the same non-determinism that makes the false-answer rate a range (0.00–0.09) rather than a clean zero — it cuts both ways, and here it blocks *correct* answers. A student uploading notes and being told "I can't find that" half the time will not trust the product.

**Fix:** the groundedness judge is too strict on short single-chunk contexts. Soften the judge prompt for short contexts, retry once on a block before refusing, and log every block so the rate is visible. Track "valid-answer block rate" in the eval harness as a first-class metric.

### 2.2 The dashboard is 100% fabricated
`dashboard/page.tsx` is a static component with **zero API calls** — no `useEffect`, no service import. Every number is a hardcoded constant:

- **GPA 3.87**, **8 enrolled courses**, **52 credits earned**, **92% onboarding**
- Fake documents ("Updated enrollment letter", "Course plan summary")
- Fake activity feed ("Transcript request approved", "10 min ago")
- Fake attendance (96%, 94%)

This is the **first screen a user sees after login**. It invents an academic record. For a faculty product this is worse than an empty state — it's misinformation. Real data exists for some of it (`/courses/mine` gives a true course count).

### 2.3 Every user is shown someone else's identity
`(protected)/layout.tsx` hardcodes the header identity:

```
Jordan Doe   /   Student Ops   /   avatar "JD"
```

Every logged-in user sees "Jordan Doe" regardless of who they are. The sidebar additionally hardcodes **"Profile completeness 84%"** and the product name renders as **"Digital Campus Admin Blueprint"**. The sidebar *does* fetch the real profile for its bottom card — so the app shows the real name and a fake name on the same screen.

### 2.4 There is no onboarding / information-gathering
Registration collects exactly **three** fields: `email`, `password`, `full_name`.

Yet the `Student` model carries `student_status`, `academic_year`, `bac_type`, `bac_score`, `interests`, `goals`, and `onboarding_completed` — and `/onboarding/status` exists and returns:

```json
{"onboarding_completed": false, "student_status": "prospective", "academic_year": null}
```

**No onboarding page exists anywhere in the frontend** (`find` for `*onboard*` returns nothing). `onboarding_completed` can never become true through the UI. Consequences:

- Every user is permanently `prospective`, so agent routing always picks Orientation — the Academic agent is unreachable.
- Prompts inject `academic_year: None`, so year-aware filtering never engages.
- `interests` / `goals` / `bac_score` are dead columns; personalisation and recommendations can't work.

The profile page can edit some of this *after* the fact, but nothing prompts the user to.

### 2.5 Errors are swallowed and replaced with a misleading message
`services/rag.py` wraps the pipeline in `except Exception:` and returns:

> *"I received your message: '…'. RAG pipeline will be connected soon."*

I hit this live: chat returned that placeholder for **95 seconds** with no logged error. The user is told the feature isn't built yet; the operator gets nothing to debug. (In my case the underlying cause was environmental, but the point stands — **any** pipeline failure surfaces as this.)

**Fix:** log the exception with traceback, return a real error state the UI can show ("something went wrong, retry"), and delete the "will be connected soon" string entirely.

---

## 3. Major issues

### 3.1 Auth guard is client-side only
Protected pages return **HTTP 200 with page-shell HTML** to unauthenticated requests; the redirect happens only after React hydrates.

```
GET /dashboard (no token) -> 200
GET /chat      (no token) -> 200
GET /courses   (no token) -> 200
GET /profile   (no token) -> 200
```

No user data leaks (the API is correctly 401), but there's a visible flash of the app shell and no protection for anyone with JS disabled or scraping HTML. **Fix:** Next.js middleware for a server-side redirect.

### 3.2 Brute-force protection is inactive
Eight rapid bad logins → `[401 × 8]`, **no 429**. The limiter is correct but **fails open**, and Redis isn't running. As currently deployed there is **no brute-force protection at all**. Either ship Redis (compose service) or fall back to an in-process limiter so the default posture isn't "off".

### 3.3 Sessions die after 30 minutes with no recovery
Token expiry is 30 minutes with **no refresh token**. My audit token expired mid-test (`401 Invalid token`). A student mid-conversation is silently logged out. The frontend now redirects to login on 401, which is correct but abrupt.

### 3.4 Latency is high
Measured, warm DB: **36.6s** first query (model load), then **2.3–4.8s**. Streaming masks it (first token ~1s) but the non-streaming `/chat` blocks the full duration. Every answer costs **two LLM round-trips** (generate + groundedness). No caching.

### 3.5 Email verification is bypassed
`AUTO_VERIFY_EMAIL=true` in `.env`. Convenient locally; in production it means **anyone can register with an email they don't own**. Must be `false` with real SMTP before launch.

### 3.6 JWT stored in `localStorage`
XSS-stealable. Should be an httpOnly, Secure, SameSite cookie.

---

## 4. Answer-quality observations

- *"Quels sont les départements de la FSB ?"* returned only **one** department (Mathématiques) with 1 citation. No single document lists all six; they're split across `dep_*` fiches. A synthesis "fact card" would fix it.
- The knowledge base still contains stale/mixed academic years (2024-25 and 2025-26 coexist) with nothing marking which is current.
- **94% of the corpus (course syllabi) remains untested** — the 80/100 benchmark covers faculty information, not course content.

---

## 5. Production-readiness checklist

| # | Item | Status |
|---|---|---|
| 1 | Course chat reliable (not 50%) | ❌ **blocker** |
| 2 | Dashboard shows real data | ❌ **blocker** |
| 3 | Real user identity in header | ❌ **blocker** |
| 4 | Onboarding flow | ❌ **blocker** |
| 5 | Errors logged, no fake placeholder | ❌ **blocker** |
| 6 | Server-side route protection | ❌ |
| 7 | Rate limiting actually active (Redis) | ❌ |
| 8 | `AUTO_VERIFY_EMAIL=false` + SMTP | ❌ |
| 9 | Refresh tokens / password reset | ❌ |
| 10 | JWT in httpOnly cookie | ❌ |
| 11 | Alembic migrations (no `create_all`) | ❌ |
| 12 | CI running both test suites | ❌ |
| 13 | Google Classroom credentials | ❌ (manual path works) |
| 14 | Error monitoring / structured logs | ❌ |
| 15 | Course-content eval (94% of corpus) | ❌ |
| 16 | Auth, IDOR, revocation, CORS | ✅ |
| 17 | RAG answers with citations | ✅ |
| 18 | Streaming | ✅ |
| 19 | Per-student course isolation | ✅ |

---

## 6. Prioritised roadmap

**P0 — before anyone demos it (~1 week)**
1. Fix the 50% course-chat refusal (soften judge on short contexts + retry-once + log blocks).
2. Replace the fake dashboard with real data from `/courses/mine`, `/chat/sessions`, `/profile` — and an honest empty state.
3. Wire the header to the real profile; delete "Jordan Doe" and "Profile completeness 84%".
4. Build the onboarding flow (status, year, bac, interests) and set `onboarding_completed`.
5. Log swallowed exceptions; remove the "will be connected soon" placeholder.

**P1 — before real users (~1 week)**
6. Next middleware for server-side auth.
7. Redis in compose (or in-process fallback) so rate limiting is on by default.
8. `AUTO_VERIFY_EMAIL=false` + working SMTP.
9. Refresh tokens + password reset.
10. Alembic migrations.
11. CI on both suites.

**P2 — hardening**
12. httpOnly cookie for JWT.
13. Course-content eval set + KB cleanup for syllabi.
14. Response caching / latency work.
15. Google Classroom verification.
16. i18n (UI is English, content French) and accessibility.

---

## 7. Honest bottom line

The engineering underneath is **better than the product on top of it**. Retrieval quality, citation grounding, per-student data isolation, token revocation and IDOR protection are all real and verified. What's missing is the last mile: a dashboard that tells the truth, an onboarding flow that collects the data the model already expects, an identity that isn't someone else's name, and an answer path that doesn't refuse half the time.

Those are days of work, not months — but they are the difference between a convincing demo and something a student can rely on. **Do not present the dashboard as functional**, and fix the course-chat reliability before the courses feature is shown at all.
