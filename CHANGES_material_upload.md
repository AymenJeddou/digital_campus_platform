# Role 2 — Real file upload for course materials (third increment)

Builds on `feature/courses-integrations` (manual courses/materials) and
`feature/courses-classroom` (Google Classroom sync). This closes the gap
flagged as "next step" after those two: until now the only way to add a
course material was `POST /courses/{course_id}/materials` with an already-
typed `content` string — there was no way to hand the assistant an actual
PDF or Word file.

## How to apply this

```bash
git checkout feature/courses-classroom
git checkout -b feature/courses-upload
# unzip this archive into the repo root, overwriting the listed files below
git add -A
git commit -m "Add real file upload (PDF/DOCX/TXT/MD) for course materials"
```

## What this delivers

- **`POST /courses/{course_id}/materials/upload`** (multipart, protected,
  requires enrollment) — accepts one `file` plus an optional `title` form
  field. Text is extracted server-side, then run through the exact same
  `course_ingestion.ingest_material` used by the manual-text path and by
  Classroom sync, so an uploaded PDF is chunked, embedded, and retrievable
  exactly like any other material — no special-casing in `/chat`.
- **`app/services/text_extraction.py`** — new, self-contained extraction
  module:
  - `.pdf` via `pypdf` (page-by-page; skips an individual unreadable page
    rather than failing the whole file; attempts a blank-password decrypt
    for encrypted-but-not-actually-locked PDFs; rejects true scanned images
    with no text layer — OCR is out of scope here, same boundary already
    flagged for Classroom's non-Doc attachments).
  - `.docx` via `python-docx` (paragraphs + table cells).
  - `.txt` / `.md` as plain text (utf-8, utf-8-sig, then latin-1 fallback).
  - Anything else → `UnsupportedFileType` → **415**. Recognized-but-empty
    or unreadable → `TextExtractionError` → **422**.
- **Size limit**: 20 MB per upload (`MAX_UPLOAD_BYTES` in `courses.py`) →
  **413** if exceeded. A 300-page ceiling on PDFs specifically, to bound
  chunking/embedding cost on a single request.
- **`CourseMaterial.source`** gains a third value, `"upload"` (alongside
  the existing `"manual"` and `"google_classroom"`), and a new
  **`original_filename`** column, so the UI can show what was actually
  uploaded and distinguish typed notes from uploaded files.

## Files changed

**New**
- `backend/app/services/text_extraction.py`
- `backend/tests/test_material_upload.py` — 8 new tests.

**Modified**
- `backend/app/api/routes/courses.py` — new `upload_course_material`
  endpoint + `MAX_UPLOAD_BYTES` constant.
- `backend/app/schemas/course.py` — `CourseMaterialResponse` gains
  `original_filename`.
- `backend/app/models/models.py` — `CourseMaterial.original_filename`.
- `backend/app/db/database.py` — `ensure_schema()` now also migrates
  `course_materials` (adds `original_filename` if the table already exists
  from an earlier increment's deploy — same pattern as the other tables in
  this function).

## New dependencies

- `pypdf` — PDF text extraction. Confirmed working (tested in this sandbox
  against a real generated PDF, not just syntax-checked).
- `python-docx` — DOCX text extraction. Same — confirmed working against a
  real generated `.docx`.

Add both to `requirements.txt`.

## Testing status

Unlike the Classroom increment, this sandbox **did** have network access to
install `pypdf`, `python-docx`, and `reportlab` (test-fixture generation
only, not a runtime dependency), so `text_extraction.py` was verified
directly — not just syntax-checked — against a real generated PDF, a real
`.docx`, plain text, an unsupported type, and a blank/no-text PDF. All
behaved as expected (see the module docstring for exact error cases).

What could **not** be run here: the endpoint-level tests in
`test_material_upload.py`, because the base FastAPI app (`app.core.config`,
`app.core.dependencies`, `app.main`, `app.services.course_ingestion`) isn't
part of either zip available in this session — same limitation noted in
`CHANGES_classroom.md`. The tests are written against the same mocking
conventions as `test_classroom.py` / `test_courses.py`. Please run for real
before merging:

```bash
cd backend
cat > .env << 'EOF'
DATABASE_URL=sqlite:///./test.db
SECRET_KEY=any-string
ALGORITHM=HS256
AUTO_VERIFY_EMAIL=false
EOF
pip install pypdf python-docx reportlab
PYTHONPATH=.. python -m pytest tests/test_material_upload.py -q
rm -f test.db .env
```

## Not in this increment (next steps for the role)

- OCR for scanned/image-only PDFs (currently rejected with a clear 422
  rather than silently ingesting nothing).
- `.pptx` support (slide exports are a common course-material format;
  same extraction approach would apply via `python-pptx`).
- Frontend upload UI (drag-and-drop / file picker on the courses screen,
  Role 3) — the endpoint is ready to be wired up.
- Applying the same extraction module to Classroom's non-Doc attachments
  (PDF/Slides materials synced from Classroom), closing the gap flagged in
  `CHANGES_classroom.md`.
