# Role 2 — PDF/DOCX Classroom attachments (fourth increment)

Builds on `feature/courses-upload` (needs `text_extraction.py` from that
branch — not re-shipped here). Closes the gap both earlier CHANGES files
flagged: Classroom attachments that aren't native Google Docs/Slides were
only represented by title/link, never actual content.

## How to apply this

```bash
git checkout feature/courses-upload
git checkout -b feature/courses-classroom-attachments
# unzip this archive into the repo root, overwriting the listed file below
git add -A
git commit -m "Extract text from PDF/DOCX Classroom attachments"
```

## What changed

`app/services/classroom_client.py`, one function (`_attachment_text`) and
its two helpers:

- `fetch_drive_doc_text` — unchanged behavior, tries Drive's `export` as
  `text/plain` (works for native Google Docs and Slides).
- New `fetch_drive_file_bytes` — downloads raw bytes via `alt=media`, for
  when a Classroom attachment is an actually-uploaded file rather than a
  native Google Doc.
- New `fetch_drive_file_text` — tries the export first, and only if that
  fails, downloads the raw bytes and runs them through the `text_extraction`
  module already added in `feature/courses-upload` (same PDF/DOCX/TXT/MD
  support, same error handling — an unsupported or unreadable attachment
  falls back to the existing title/link placeholder, exactly as before).

`_attachment_text` now calls `fetch_drive_file_text` instead of
`fetch_drive_doc_text` directly. No other file changes — this reuses the
sync/ingestion pipeline as-is.

## Testing status

No FastAPI app needed for this one — verified directly in this sandbox with
mocked `requests.get` calls against the real `text_extraction` module and a
real generated PDF: confirmed (1) a non-native attachment (PDF) is
downloaded and its text extracted, (2) a native Google Doc still goes
through `export` unaffected, (3) an unsupported attachment type falls back
to `None` (→ existing title/link placeholder), not an exception.

## Not in this increment

- `.pptx` still isn't handled by `text_extraction` itself — a Slides file
  that was *uploaded* as a raw `.pptx` (not created natively in Slides)
  would still fall back to the placeholder. Native Google Slides already
  work via `export`.
- OCR for scanned PDF attachments — same boundary as the upload endpoint.
