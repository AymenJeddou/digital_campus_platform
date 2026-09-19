"""Google Classroom sync: turns a connected student's Classroom courses,
coursework, courseWorkMaterials, and announcements into local `Course` /
`StudentCourse` / `CourseMaterial` rows, then reuses the existing
`course_ingestion.ingest_material` to chunk + embed them — the same path
manual uploads go through, so retrieval and `/chat` course-scoping need no
special-casing for the Classroom source.
"""

from __future__ import annotations

import logging
import threading
import time
import uuid
from typing import Any, Callable, Optional

from sqlalchemy.orm import Session

from app.services import classroom_client
from app.services.course_ingestion import ingest_material
from app.services.token_crypto import decrypt_token, encrypt_token

logger = logging.getLogger(__name__)

TOKEN_REFRESH_SKEW_SECONDS = 60

# --- Background sync jobs ---------------------------------------------------
# A full sync fetches every course's coursework/materials/announcements and
# chunk+embeds each item inline (seconds per item). Doing that inside the HTTP
# request blocks it for minutes, so the request "hangs". Instead we run the sync
# on a daemon thread and expose its live state here; the frontend polls
# GET /courses/classroom/status. State is in-memory (single uvicorn worker); a
# restart mid-sync simply resets to idle — the connection and any already-ingested
# materials persist, and the user can sync again.
_JOBS: dict[str, dict[str, Any]] = {}
_LOCK = threading.Lock()


def _update_job(key: str, **fields: Any) -> None:
    with _LOCK:
        job = _JOBS.get(key)
        if job:
            job.update(fields)


def get_job_state(student_id: uuid.UUID) -> Optional[dict[str, Any]]:
    """Return a copy of the current sync-job state for a student, or None."""
    with _LOCK:
        job = _JOBS.get(str(student_id))
        return dict(job) if job else None


def start_sync(student_id: uuid.UUID, account_id: uuid.UUID) -> dict[str, Any]:
    """Start a background sync for the student (no-op if one is already running).

    Returns the job state so the caller can respond immediately.
    """
    key = str(student_id)
    with _LOCK:
        existing = _JOBS.get(key)
        if existing and existing.get("status") == "running":
            return dict(existing)
        job = {
            "status": "running",
            "started_at": time.time(),
            "finished_at": None,
            "courses_synced": 0,
            "materials_synced": 0,
            "materials_failed": 0,
            "error": None,
        }
        _JOBS[key] = job
    threading.Thread(target=_run_job, args=(key, str(account_id)), daemon=True).start()
    return dict(job)


def _run_job(key: str, account_id: str) -> None:
    # A background thread must use its OWN session, never the request's.
    from app.db.database import SessionLocal  # noqa: PLC0415
    from app.models.models import GoogleClassroomAccount, Student  # noqa: PLC0415

    db = SessionLocal()
    try:
        student = db.query(Student).filter(Student.id == uuid.UUID(key)).first()
        account = (
            db.query(GoogleClassroomAccount)
            .filter(GoogleClassroomAccount.id == uuid.UUID(account_id))
            .first()
        )
        if not student or not account:
            _update_job(key, status="error", error="Account not found", finished_at=time.time())
            return

        def on_progress(courses_synced: int, materials_synced: int, materials_failed: int) -> None:
            _update_job(
                key,
                courses_synced=courses_synced,
                materials_synced=materials_synced,
                materials_failed=materials_failed,
            )

        result = sync_student_classroom(db, student, account, on_progress=on_progress)
        _update_job(
            key,
            status="success",
            courses_synced=result["courses_synced"],
            materials_synced=result["materials_synced"],
            materials_failed=result["materials_failed"],
            finished_at=time.time(),
        )
    except classroom_client.ClassroomAPIError as exc:
        logger.exception("Classroom background sync failed (API error)")
        _update_job(key, status="error", error=str(exc), finished_at=time.time())
    except Exception as exc:  # noqa: BLE001 - report any failure to the poller
        logger.exception("Classroom background sync failed")
        _update_job(key, status="error", error=str(exc), finished_at=time.time())
    finally:
        db.close()


def get_valid_access_token(db: Session, account) -> str:
    """Return a usable access token, refreshing it first if it has expired."""
    if account.token_expires_at and account.token_expires_at > time.time() + TOKEN_REFRESH_SKEW_SECONDS:
        return decrypt_token(account.access_token)

    refresh_token = decrypt_token(account.refresh_token)
    token_set = classroom_client.refresh_access_token(refresh_token)
    account.access_token = encrypt_token(token_set.access_token)
    account.token_expires_at = token_set.expires_at
    db.commit()
    return token_set.access_token


def _get_or_create_course(db: Session, student_id: uuid.UUID, classroom_course: dict):
    from app.models.models import Course, StudentCourse  # noqa: PLC0415

    external_id = classroom_course["id"]
    enrollment = (
        db.query(StudentCourse)
        .filter(
            StudentCourse.student_id == student_id,
            StudentCourse.source == "google_classroom",
            StudentCourse.external_id == external_id,
        )
        .first()
    )
    if enrollment:
        course = db.query(Course).filter(Course.id == enrollment.course_id).first()
        # Keep the local course name/section in sync with Classroom.
        course.name = classroom_course.get("name", course.name)
        course.code = classroom_course.get("section") or course.code
        db.commit()
        return course, enrollment

    course = Course(
        name=classroom_course.get("name", "Cours Google Classroom"),
        code=classroom_course.get("section"),
        description=classroom_course.get("descriptionHeading") or classroom_course.get("description"),
    )
    db.add(course)
    db.commit()
    db.refresh(course)

    enrollment = StudentCourse(
        student_id=student_id,
        course_id=course.id,
        source="google_classroom",
        external_id=external_id,
    )
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return course, enrollment


def _get_or_create_material(db: Session, student_id: uuid.UUID, course_id: uuid.UUID, external_id: str, title: str, content: str):
    from app.models.models import CourseMaterial  # noqa: PLC0415

    material = (
        db.query(CourseMaterial)
        .filter(
            CourseMaterial.student_id == student_id,
            CourseMaterial.course_id == course_id,
            CourseMaterial.source == "google_classroom",
            CourseMaterial.external_id == external_id,
        )
        .first()
    )
    if material:
        material.title = title
        material.content = content
        material.status = "pending"
        db.commit()
        return material

    material = CourseMaterial(
        course_id=course_id,
        student_id=student_id,
        title=title,
        content=content,
        source="google_classroom",
        external_id=external_id,
        status="pending",
    )
    db.add(material)
    db.commit()
    db.refresh(material)
    return material


def _sync_course_items(
    db: Session,
    access_token: str,
    student_id: uuid.UUID,
    course_id: uuid.UUID,
    classroom_course_id: str,
    on_material: Optional[Callable[[], None]] = None,
    on_failed: Optional[Callable[[], None]] = None,
) -> tuple[int, int]:
    """Ingest a course's items. Returns (synced, failed).

    Each item is processed independently: a single un-parseable attachment
    (e.g. an encrypted/password-protected PDF, a corrupt file, or a Drive
    permission error) is logged and skipped instead of aborting the whole sync.
    """
    materials_synced = 0
    materials_failed = 0

    for kind, fetcher in (
        ("courseWork", classroom_client.list_coursework),
        ("courseWorkMaterial", classroom_client.list_coursework_materials),
        ("announcement", classroom_client.list_announcements),
    ):
        for item in fetcher(access_token, classroom_course_id):
            item_id = item.get("id", "?")
            try:
                text = classroom_client.item_to_material_text(access_token, item)
                if not text.strip():
                    continue
                title = item.get("title") or f"{kind} sans titre"
                material = _get_or_create_material(
                    db, student_id, course_id,
                    external_id=item_id,
                    title=title,
                    content=text,
                )
                ingest_material(db, material)
            except Exception as exc:  # noqa: BLE001 - one bad item must not stop the sync
                # Roll back any half-applied write for this item so the session
                # stays usable for the next item, then skip it.
                db.rollback()
                materials_failed += 1
                logger.warning(
                    "Skipping Classroom %s item %s (course=%s): %s: %s",
                    kind, item_id, course_id, type(exc).__name__, exc,
                )
                if on_failed is not None:
                    on_failed()
                continue

            materials_synced += 1
            if on_material is not None:
                on_material()  # report incremental progress to the poller

    logger.info(
        "Course %s: synced %d materials, skipped %d (student=%s)",
        course_id, materials_synced, materials_failed, student_id,
    )
    return materials_synced, materials_failed


def sync_student_classroom(
    db: Session,
    student,
    account,
    on_progress: Optional[Callable[[int, int, int], None]] = None,
) -> dict[str, Any]:
    """Full sync for one student: courses + their coursework/materials/announcements.

    ``on_progress(courses_synced, materials_synced, materials_failed)`` is called
    (when provided) as each item is processed and after each course, so a
    background caller can surface live progress. Individual un-parseable items are
    skipped (counted in ``materials_failed``), never aborting the run.
    """
    access_token = get_valid_access_token(db, account)

    courses_synced = 0
    materials_synced = 0
    materials_failed = 0
    synced_courses: list[dict[str, Any]] = []

    for classroom_course in classroom_client.list_courses(access_token):
        course, _enrollment = _get_or_create_course(db, student.id, classroom_course)

        def _on_material() -> None:
            nonlocal materials_synced
            materials_synced += 1
            if on_progress is not None:
                on_progress(courses_synced, materials_synced, materials_failed)

        def _on_failed() -> None:
            nonlocal materials_failed
            materials_failed += 1
            if on_progress is not None:
                on_progress(courses_synced, materials_synced, materials_failed)

        count, _failed = _sync_course_items(
            db, access_token, student.id, course.id, classroom_course["id"],
            on_material=_on_material, on_failed=_on_failed,
        )
        courses_synced += 1
        synced_courses.append({"id": course.id, "name": course.name, "materials_synced": count})
        if on_progress is not None:
            on_progress(courses_synced, materials_synced, materials_failed)

    account.last_synced_at = time.time()
    db.commit()

    return {
        "courses_synced": courses_synced,
        "materials_synced": materials_synced,
        "materials_failed": materials_failed,
        "courses": synced_courses,
    }
