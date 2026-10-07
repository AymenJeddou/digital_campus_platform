# Product

FSB Nexus / Digital Campus: an AI assistant for the Faculté des Sciences de Bizerte (FSB, Université de Carthage, Tunisia) that answers students' questions from the faculty's official documents, with sources.

## Platform

web

## Stack

Next.js 16 (App Router, React 19, Tailwind CSS 4) frontend; FastAPI + PostgreSQL/pgvector backend; Mistral or Gemini for generation.

## Users

- **Prospective students** (bac holders, often 18–19) choosing a licence or master at FSB: admission conditions, programmes, scores, deadlines.
- **Enrolled students** (L1 → Master/Doctorat) asking about their courses, the academic calendar, administrative procedures (inscription, bourses, attestations, stages), and the content of their own course materials.
- **Faculty staff (admin role)** who upload knowledge-base documents and read feedback / unanswered questions.

## Product Purpose

Replace "ask a friend who asked the secretariat" with a sourced answer in seconds. Every factual answer cites the official document and page it comes from; when the documents don't cover a question, the assistant says so rather than guessing.

## Positioning

Student-made, friendly, peer-to-peer: it should feel like a well-informed older student who always shows you the paper, not like an administration portal or a SaaS product.

## Operating Context

Mostly phones (Android, mid-range), on campus Wi-Fi or mobile data, often between classes or in the evening at home. Desktop use for longer study sessions with course materials. Light and dark both matter (evening use).

## Capabilities and Constraints

- Chat with streamed answers, inline citations, a source viewer, regenerate / stop, history.
- Courses: add courses manually or via Google Classroom; upload PDF/DOCX/PPTX/TXT/MD materials; ask questions scoped to one course.
- Onboarding: status (prospective / enrolled), academic year, FSB programme, bac type/score, interests, goals.
- Notifications: Classroom deadlines and official academic-calendar dates.
- Admin: knowledge-base upload, feedback and unanswered-question review.
- No telemetry/analytics beyond the app's own feedback.

## Brand Commitments

- Languages: French (default) and Arabic (full right-to-left layout). Answers follow the question's language.
- Friendly "tu" register in French, warm but never childish.
- Never claim features that don't exist; never invent facts about the faculty.
- No official FSB logo is used (none provided); the product has its own mark.

## Evidence on Hand

- The real knowledge base (~3.7k chunks): licence and master offer, department and coordinator pages, regulation forms, university calendar, bourses, internships.
- Evaluation: hit@5 0.50 → 0.90 after hybrid search; 100-question test reports in `docs/`.

## Product Principles

1. Sources first: the citation is part of the answer, not a footnote.
2. Honest refusals beat confident guesses.
3. Fast on a phone: the first answer token matters more than decoration.
4. One student's private course material is never visible to anyone else.

## Accessibility & Inclusion

WCAG 2.1 AA. Bilingual LTR/RTL. Keyboard reachable everything, visible focus, reduced-motion respected, 44px touch targets on mobile.
