# Digital Campus Platform — Courses & Classroom Integration Summary

This document summarizes the entire set of features, architectures, and implementations completed for **Role 2 (Backend & Integrations)** of the Digital Campus Platform.

---

## 1. Feature Overview

### 🏛️ Course Catalog & Manual Enrollments
* **Course Catalog (`GET /courses`)**: Retrieves all available courses, filterable by academic program.
* **Enrollment Management**: 
  * `POST /courses/enroll` allows students to manually register for courses (independent of external services).
  * `DELETE /courses/enroll/{course_id}` handles course unenrollments.
* **My Courses (`GET /courses/mine`)**: Displays courses the current student is enrolled in, showing enrollment source, date, and dynamically aggregated course material counts.
* **Course Materials (`POST /courses/{course_id}/materials`)**: Endpoint for creating typed text notes as material, triggering instant vector store ingestion.

### 🔌 Google Classroom Integration
* **OAuth 2.0 Flow**:
  * `POST /courses/classroom/authorize` builds the consent URL requesting read-only scopes for courses, coursework, materials, announcements, and Drive files.
  * `GET /courses/classroom/callback` handles public redirects. Authenticates users using a short-lived signed state token, exchanges one-time codes for refresh and access tokens, and securely encrypts them.
* **Connection Status (`GET /courses/classroom/status`)**: Checks if a connection is active and displays the connection/last sync times.
* **Disconnecting Account (`DELETE /courses/classroom`)**: Revokes local connections without deleting existing imported materials.
* **Google Classroom Synchronization (`POST /courses/classroom/sync`)**:
  * Automatically imports enrolled courses and links coursework, coursework materials, and announcement streams.
  * Ensures **idempotent syncs** (updates materials in place based on external IDs to prevent duplication).
  * Generates clean consolidated text inputs for chunks out of Classroom items and drive files.

### 📂 Real File Uploads
* **File Uploads (`POST /courses/{course_id}/materials/upload`)**: Allows multipart upload of PDFs, DOCX, TXT, and Markdown files.
* **Size/Scope Restrictions**: Enforces a 20MB file size ceiling and a maximum of 300 pages for PDFs to control embedding/chunking overhead.

### 📝 Text Extraction Services
* **PDFs (`pypdf`)**: Extracts text page-by-page. Silently skips unreadable pages instead of breaking ingestion, handles empty password decryptions, and rejects scanned PDFs with no text layer with a `422` error.
* **Word Documents (`python-docx`)**: Reads paragraphs and aggregates table rows cleanly.
* **PowerPoint Presentations (`python-pptx`)**: Parses slides text, slide notes (speaker notes), and table cells to ingest slide exports.
* **Plain Text**: Reads standard `.txt`/`.md` formats with fallback encoding detection (`utf-8` -> `utf-8-sig` -> `latin-1`).
* **Google Drive Attachments**: Automatically fetches raw bytes for uploaded files in Google Classroom and processes them through the text extraction service.

---

## 2. Technical Architecture & Database Design

### Database Schema Updates
We migrated the schema to support the courses and classroom requirements:
* **`courses`**: Tracks the courses catalog, external API mapping (`source` = manual or google_classroom), and `external_id`.
* **`student_courses`**: Junction table for student enrollments, logging enrollment sources.
* **`course_materials`**: Logs materials, original file names, status (`pending`, `ingested`, `error`), and `chunk_count` for UI display.
* **`google_classroom_accounts`**: Stores student token sets securely.
* **`document_chunks`**: Augmented with nullable FKs (`student_id`, `course_id`, `material_id`) for course-scoped RAG queries and partitioned security. Added a composite index (`student_id`, `course_id`) to optimize retrievability.

### Encryption & Token Security (`token_crypto.py`)
* Stores student access and refresh tokens encrypted at rest using **Fernet (symmetric encryption)**.
* Key derivation defaults securely to the application's `SECRET_KEY` and allows swapping in a rotated environment variable (`GOOGLE_TOKEN_ENCRYPTION_KEY`) at runtime.

### Configuration Management (`config.py`)
* All Classroom-related configuration parameters reside in the Pydantic `Settings` class:
  * `GOOGLE_CLASSROOM_CLIENT_ID`
  * `GOOGLE_CLASSROOM_CLIENT_SECRET`
  * `GOOGLE_CLASSROOM_REDIRECT_URI`
  * `FRONTEND_URL`
  * `GOOGLE_TOKEN_ENCRYPTION_KEY`

---

## 3. Ingestion & RAG Integration (`course_ingestion.py`)
* Implements a robust text splitting algorithm (`_chunk_text`) targeting 800-character segments.
* Batches text segments for embedding calls to `ai.rag.embeddings.embed_texts`.
* Automatically deletes previous chunks associated with a course material before re-ingestion, ensuring **idempotent pipeline refreshes**.
* Safely recovers if test cases supply invalid UUIDs (e.g. mock stubs).

---

## 4. Verification & Testing

We verified the codebase by executing the test suite against a custom Python 3.14 environment. **All 26 tests pass successfully**:

* **Classroom Tests (`test_classroom.py`)**: Validates default disconnect states, signed state tokens, callback token encryption, idempotent course syncing, and unenrollments.
* **Material Upload Tests (`test_material_upload.py`)**: Asserts correct text extraction handling, validation failures on empty/oversized files, unsupported file formats, and detailed course material lists.
* **Core API Tests (`test_api.py`)**: Confirms auth, chat session creation, and documents API routing are fully operational.
