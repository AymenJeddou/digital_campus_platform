# Role 2 — Google Classroom integration (second increment)

Builds on the manual courses/materials increment (`feature/courses-integrations`,
see the section below). This increment adds the target automated source per
the blueprint (6.2): "Implement the Google Classroom integration
(authorization, retrieval of the student's courses, coursework, and
materials) as the target automated source."

## How to apply this

```bash
# on top of feature/courses-integrations
git checkout -b feature/courses-classroom
# unzip this archive into the repo root, overwriting the listed files below
git add -A
git commit -m "Add Google Classroom integration: OAuth, sync, course-scoped ingestion"
```

## What this delivers

- **OAuth 2.0 authorization flow** (read-only scopes: courses, coursework,
  courseWorkMaterials, announcements, drive.readonly for Doc attachments):
  - `POST /courses/classroom/authorize` (protected) — returns the Google
    consent-screen URL. The frontend redirects the browser there.
  - `GET /courses/classroom/callback` (public — Google redirects the browser
    here with no bearer token, so it's exempted from the auth-required
    middleware and instead authenticates via a short-lived signed `state`
    value). Redirects back to `{FRONTEND_URL}/courses?classroom=connected|error|retry`.
- **`GET /courses/classroom/status`** — whether the student is connected, and
  when they last synced.
- **`POST /courses/classroom/sync`** — pulls the student's active Classroom
  courses, then for each one: courseWork, courseWorkMaterials, and
  announcements. Each item becomes a `CourseMaterial` (title + description +
  best-effort attachment text — Google Docs are exported as plain text via
  Drive; other attachment types are represented by title/link only, same
  limitation as the file-upload item already flagged as future work) and is
  run through the *existing* `course_ingestion.ingest_material` — no special
  casing needed in retrieval or `/chat`, since a Classroom-sourced chunk
  looks exactly like a manually-uploaded one (`student_id` + `course_id` +
  `material_id`). Re-running sync updates in place (matched by Classroom's
  own item id) rather than duplicating.
- **`DELETE /courses/classroom`** — disconnects (stops future syncs; leaves
  already-synced courses/materials in place, consistent with unenrolling
  being a separate, explicit action).
- **New model**: `GoogleClassroomAccount` (one per student) — encrypted
  access/refresh token + expiry. See "Token storage" below.
- **Course/enrollment reuse**: a synced Classroom course becomes a normal
  `Course` + `StudentCourse` row (`source="google_classroom"`,
  `external_id=<classroom course id>`), so it shows up in `/courses/mine`
  and is chat-scopable exactly like a manually-enrolled course.

## Token storage — flagged for Role 4

`app/services/token_crypto.py` encrypts tokens at rest with a key derived
from the existing `SECRET_KEY` so this increment doesn't require new secret
provisioning to work. The blueprint assigns "secure token storage" to Role 4
(6.4). Swapping in a dedicated, rotated `GOOGLE_TOKEN_ENCRYPTION_KEY` from a
secrets manager is a one-line change in `_get_fernet()` — flagging this
explicitly rather than treating the current default as final.

## New environment variables

```
GOOGLE_CLASSROOM_CLIENT_ID=...
GOOGLE_CLASSROOM_CLIENT_SECRET=...
GOOGLE_CLASSROOM_REDIRECT_URI=https://<api-host>/courses/classroom/callback
FRONTEND_URL=https://<app-host>            # where the callback redirects back to
GOOGLE_TOKEN_ENCRYPTION_KEY=...            # optional, see above — falls back to SECRET_KEY-derived key
```

These are read directly via `os.environ` in `classroom_client.py` rather
than added to `app/core/config.py`'s `Settings` class, since that file
wasn't part of the files shared for this increment and guessing its exact
shape risked breaking it. Moving them into `Settings` for consistency is a
5-minute follow-up once merged against the real file.

## New dependencies

- `cryptography` (token encryption) — already present in this sandbox;
  confirm it's in `requirements.txt`.
- `PyJWT` (signs the OAuth `state` param) — used here as a self-contained
  choice; if the existing `auth` module already signs JWTs with
  `python-jose` instead, either library works (both produce standard
  HS256-signed JWTs against the same `SECRET_KEY`), but consolidating on one
  is worth doing as a follow-up for consistency.

## Files changed

**New**
- `backend/app/services/classroom_client.py` — OAuth + Classroom/Drive REST calls.
- `backend/app/services/token_crypto.py` — Fernet encrypt/decrypt for stored tokens.
- `backend/app/services/classroom_sync.py` — courses/materials sync + ingestion.
- `backend/tests/test_classroom.py` — 8 new tests.

**Modified**
- `backend/app/models/models.py` — `GoogleClassroomAccount`.
- `backend/app/schemas/course.py` — Classroom request/response schemas.
- `backend/app/api/routes/courses.py` — the 5 endpoints above.
- `backend/app/main.py` — exempts the OAuth callback from the auth-required middleware.

## Testing status — please re-run before merging

This increment was built in a sandbox **without network access**, so
`fastapi`/`sqlalchemy`/`pydantic` etc. weren't installable here and the test
suite could not actually be executed this time (unlike the previous
increment). Every file was syntax-checked with `python -m py_compile` and
the tests were written against the same mocking conventions as
`test_courses.py` (stubbing `classroom_client` calls and the embeddings
module), but please run the real suite before merging:

```bash
cd backend
cat > .env << 'EOF'
DATABASE_URL=sqlite:///./test.db
SECRET_KEY=any-string
ALGORITHM=HS256
AUTO_VERIFY_EMAIL=false
EOF
PYTHONPATH=.. python -m pytest tests/test_classroom.py -q
rm -f test.db .env
```

## Not in this increment (next steps for the role)

- Non-Doc attachment text extraction (PDFs, Slides, uploaded files) — same
  scope boundary as manual file upload, tracked together.
- Frontend courses screen showing "Connect Google Classroom" / sync status
  (Role 3, per the blueprint's "provide, together with Role 3, a courses
  screen").
- Moving the new env vars into `app/core/config.py::Settings` once this is
  merged against the real file.
- A background/scheduled sync instead of the current on-demand
  `POST /courses/classroom/sync` (nice-to-have, not required by the
  blueprint's definition of done).
