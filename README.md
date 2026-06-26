# Digital Campus Platform

Backend API for student authentication, profile management, conversations, and document-backed RAG responses.

## Endpoints

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

The verification token is sent by email when SMTP settings are configured. It is not returned by the API response.

`POST /auth/verify`

Request:
```json
{
	"token": "<verification_token>"
}
```

`POST /auth/login`

Form data:
`username=student@example.com` and `password=testpass123`

### Profile

`GET /profile`

`PATCH /profile`

`PATCH /profile/academic-year`

`GET /profile/onboarding/status`

`GET /onboarding/status`

Example update body:
```json
{
	"full_name": "Updated Name",
	"student_status": "admin"
}
```

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

Chat replies are routed through the configured `RAG_PIPELINE_HANDLER` when present, with a fallback response otherwise. The handler can return `{ "answer": "...", "citations": [...] }`.

### Documents

`GET /documents`

`POST /documents`

`POST /documents` requires `student_status = "admin"`.

Example upload:
```json
{
	"title": "Student Handbook",
	"content": "Campus rules and procedures"
}
```

## Schema

The backend defines the 11 tables from the blueprint: students, programs, departments, courses, documents, document_chunks, admission_scores, recommendations, chat_sessions, chat_messages, and audit_logs.

The student model includes the onboarding fields `student_status`, `academic_year`, `interests`, `goals`, `enrollment_date`, and `onboarding_completed`.