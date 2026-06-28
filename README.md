# Digital Campus Platform

Backend API for a digital campus experience built with FastAPI, SQLAlchemy, and JWT authentication. The service covers student registration and verification, profile and onboarding data, chat sessions backed by a pluggable RAG hook, and document management for administrators.

## What This Backend Does

This project implements the API layer for a campus assistant platform. The main pieces are:

- student account creation with email verification
- login with bearer-token authentication
- profile retrieval and onboarding updates
- chat sessions that persist user and assistant messages
- document listing and admin-only uploads
- startup schema creation plus lightweight database migration reconciliation
- a configurable RAG integration point with a safe fallback response when the pipeline is not connected

## Architecture

The application starts in `backend/app/main.py`, where it:

- creates the SQLAlchemy tables on startup
- runs schema reconciliation for existing PostgreSQL databases
- configures permissive CORS
- protects the `/profile`, `/chat`, `/documents`, and `/onboarding/status` routes by requiring an `Authorization` header
- registers the auth, profile, chat, and document routers

The backend is organized into:

- `app/api/routes/` for route handlers
- `app/core/` for configuration, JWT helpers, and authenticated-user dependencies
- `app/db/` for SQLAlchemy engine/session setup and schema reconciliation
- `app/models/` for database models
- `app/schemas/` for request and response validation models
- `app/services/` for email delivery and chat/RAG behavior

## Features We Implemented

### Authentication Flow

The auth flow is a three-step process:

1. `POST /auth/register` creates a student record with a hashed password and `is_verified = false`.
2. A verification token is generated with a dedicated JWT purpose: `email_verification`.
3. `POST /auth/verify` marks the student as verified.
4. `POST /auth/login` returns a bearer token only after verification succeeds.

Important details:

- verification tokens are not returned in the API response
- if SMTP is configured, the verification token is sent by email
- login tokens use a different JWT purpose: `login`
- protected endpoints reject tokens that are not login tokens

### Profile and Onboarding

The profile module exposes:

- `GET /profile` to fetch the authenticated student record
- `PATCH /profile` to update the allowed profile fields
- `PATCH /profile/academic-year` to update the academic year separately
- `GET /profile/onboarding/status` to return the student onboarding state
- `GET /onboarding/status` as a top-level alias for the same onboarding data

Editable profile fields include:

- `full_name`
- `interests`
- `goals`
- `student_status` for non-privileged values only

The backend blocks privileged status changes through the profile endpoint so those values cannot be elevated casually through a normal update request.

### Chat Sessions

The chat module stores conversation history in the database:

- `POST /chat` creates a session when no `session_id` is provided
- `POST /chat` appends a user message and an assistant message to `chat_messages`
- `GET /chat/sessions` lists the current student’s chat sessions
- `GET /chat/sessions/{session_id}/messages` returns the messages for one session

Chat answers are generated through `app/services/rag.py`:

- if `RAG_PIPELINE_HANDLER` is configured, the backend imports and calls that handler dynamically
- the handler may return a string or a dictionary with `answer` and `citations`
- if the handler is missing or fails, the service returns a safe fallback response instead of breaking the API

### Documents

The document module supports:

- `GET /documents` to list stored documents
- `POST /documents` to upload a document

Document uploads are restricted to admin users through the `role` field on the student record.

### Database Model

The SQLAlchemy model layer defines the core campus tables:

- `students`
- `programs`
- `departments`
- `courses`
- `documents`
- `document_chunks`
- `admission_scores`
- `recommendations`
- `chat_sessions`
- `chat_messages`
- `audit_logs`

The `students` table includes onboarding-related fields such as `student_status`, `academic_year`, `interests`, `goals`, `enrollment_date`, `onboarding_completed`, `is_verified`, and `role`.

`document_chunks` is prepared for vector search use cases and stores embeddings as a PostgreSQL vector when available, or JSON otherwise.

## API Reference

### Root

`GET /`

Returns a simple health-style message confirming the API is running.

### Auth

`POST /auth/register`

Request:

```json
{
	"email": "student@example.com",
	"password": "testpass123",
	"full_name": "Student Name"
}
```

Response:

```json
{
	"message": "Account created successfully",
	"email": "student@example.com"
}
```

`POST /auth/verify`

Request:

```json
{
	"token": "<verification_token>"
}
```

`POST /auth/login`

Form data:

- `username=student@example.com`
- `password=testpass123`

Response:

```json
{
	"access_token": "<jwt>",
	"token_type": "bearer"
}
```

### Profile

`GET /profile`

`PATCH /profile`

Example request:

```json
{
	"full_name": "Updated Name",
	"interests": ["AI", "mathematics"],
	"goals": ["join a program", "track progress"]
}
```

`PATCH /profile/academic-year`

Example request:

```json
{
	"academic_year": "L2"
}
```

`GET /profile/onboarding/status`

`GET /onboarding/status`

### Chat

`POST /chat`

Request:

```json
{
	"message": "Hello, what courses should I take?"
}
```

Response:

```json
{
	"session_id": "<uuid>",
	"answer": "RAG response...",
	"citations": []
}
```

`GET /chat/sessions`

`GET /chat/sessions/{session_id}/messages`

### Documents

`GET /documents`

`POST /documents`

Example request:

```json
{
	"title": "Student Handbook",
	"content": "Campus rules and procedures"
}
```

## Configuration

The backend reads its settings from a `.env` file through `pydantic-settings`.

Required values:

- `DATABASE_URL`
- `SECRET_KEY`

Optional values:

- `ALGORITHM` defaults to `HS256`
- `ACCESS_TOKEN_EXPIRE_MINUTES` defaults to `30`
- `SMTP_HOST`
- `SMTP_PORT` defaults to `587`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SMTP_FROM_EMAIL`
- `SMTP_USE_TLS` defaults to `true`
- `RAG_PIPELINE_HANDLER`

The RAG handler should be provided as `module.path:function_name`.

## Email Verification

The email service in `app/services/email.py` sends a verification message only when SMTP is configured.

- if `SMTP_HOST` is not set, the send step is skipped safely
- TLS and SSL are both supported through configuration
- the verification email includes the token and the `/auth/verify` instruction

## Testing

Integration tests live in `backend/tests/test_api.py`. They cover:

- registration without exposing verification tokens in responses
- verification-token isolation from login tokens
- login refusal before verification
- profile retrieval and updates
- onboarding status access
- protected route checks
- chat session persistence
- admin-only document upload
- rejection of non-admin document uploads

Run the tests from the `backend` directory:

```bash
./venv/bin/python -m pytest tests/test_api.py -q
```

## Local Development

1. Create and activate a Python virtual environment in `backend/`.
2. Install the dependencies from `backend/requirements.txt`.
3. Set the required environment variables in `.env`.
4. Start the API with Uvicorn.

Example:

```bash
uvicorn app.main:app --reload
```

## Notes

- The backend is written as a focused API service, not a full frontend application.
- The RAG flow is intentionally pluggable so the assistant can be wired into a real retrieval pipeline later without changing the chat route contract.
- Startup schema reconciliation exists to make the code more tolerant of older database states during development and testing.
