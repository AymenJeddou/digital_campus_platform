"""Google Classroom sync: turns a connected student's Classroom courses,
coursework, courseWorkMaterials, and announcements into local `Course` /
`StudentCourse` / `CourseMaterial` rows, then reuses
`course_ingestion.ingest_material` to chunk + embed them, so retrieval and
course-scoped chat need no special-casing for the Classroom source.

A full sync chunk+embeds every item (seconds each), so it runs on a daemon
thread. Its progress is stored on the GoogleClassroomAccount row, so polling
works across workers and a restart can't leave a phantom "running" job (a run
older than STALE_AFTER_SECONDS is reported as failed and can be restarted).
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
STALE_AFTER_SECONDS = 3600


def effective_status(account) -> str:
    status = account.sync_status or "idle"
    if status == "running" and (account.sync_started_at or 0) < time.time() - STALE_AFTER_SECONDS:
        return "error"  # the worker died mid-sync
    return status


def _update(account_id: uuid.UUID, **fields: Any) -> None:
    """Write sync progress with a short-lived session of its own."""
    from app.db.database import SessionLocal  # noqa: PLC0415
    from app.models.models import GoogleClassroomAccount  # noqa: PLC0415

    db = SessionLocal()
    try:
        db.query(GoogleClassroomAccount).filter(GoogleClassroomAccount.id == account_id).update(fields)
        db.commit()
    finally:
        db.close()


def start_sync(db: Session, account) -> None:
    """Start a background sync (no-op if one is already running)."""
    if effective_status(account) == "running":
        return
    account.sync_status = "running"
    account.sync_started_at = time.time()
    account.sync_courses_synced = 0
    account.sync_materials_synced = 0
    account.sync_materials_failed = 0
    account.sync_error = None
    db.commit()
    threading.Thread(target=_run_job, args=(account.id,), daemon=True).start()


def _run_job(account_id: uuid.UUID) -> None:
    # A background thread must use its OWN session, never the request's.
    from app.db.database import SessionLocal  # noqa: PLC0415
    from app.models.models import GoogleClassroomAccount, Student  # noqa: PLC0415

    db = SessionLocal()
    try:
        account = db.query(GoogleClassroomAccount).filter(GoogleClassroomAccount.id == account_id).first()
        student = account and db.query(Student).filter(Student.id == account.student_id).first()
        if not student:
            _update(account_id, sync_status="error", sync_error="Account not found")
            return

        def on_progress(courses: int, synced: int, failed: int) -> None:
            _update(account_id, sync_courses_synced=courses, sync_materials_synced=synced,
                    sync_materials_failed=failed)

        result = sync_student_classroom(db, student, account, on_progress=on_progress)
        _update(
            account_id,
            sync_status="success",
            sync_courses_synced=result["courses_synced"],
            sync_materials_synced=result["materials_synced"],
            sync_materials_failed=result["materials_failed"],
        )
    except Exception as exc:  # noqa: BLE001 - report any failure to the poller
        logger.exception("Classroom background sync failed")
        _update(account_id, sync_status="error", sync_error=str(exc)[:500])
    finally:
        db.close()


def get_valid_access_token(db: Session, account) -> str:
    """Return a usable access token, refreshing it first if it has expired."""
    if account.token_expires_at and account.token_expires_at > time.time() + TOKEN_REFRESH_SKEW_SECONDS:
        return decrypt_token(account.access_token)

    token_set = classroom_client.refresh_access_token(decrypt_token(account.refresh_token))
    account.access_token = encrypt_token(token_set.access_token)
    account.token_expires_at = token_set.expires_at
    db.commit()
    return token_set.access_token


def _get_or_create_course(db: Session, student_id: uuid.UUID, classroom_course: dict):
    """Each student gets their own private Course row per Classroom course
    (source="google_classroom"), so one student's Classroom never shows up in
    the shared catalog or in another student's view."""
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
        course.name = classroom_course.get("name", course.name)
        course.code = classroom_course.get("section") or course.code
        db.commit()
        return course, enrollment

    course = Course(
        name=classroom_course.get("name", "Cours Google Classroom"),
        code=classroom_course.get("section"),
        description=classroom_course.get("descriptionHeading") or classroom_course.get("description"),
        source="google_classroom",
        external_id=external_id,
    )
    db.add(course)
    db.flush()
    enrollment = StudentCourse(
        student_id=student_id, course_id=course.id, source="google_classroom", external_id=external_id,
    )
    db.add(enrollment)
    db.commit()
    return course, enrollment


def _get_or_create_material(db: Session, student_id, course_id, external_id: str, title: str, content: str, due_at):
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
    if not material:
        material = CourseMaterial(
            course_id=course_id, student_id=student_id, source="google_classroom", external_id=external_id,
        )
        db.add(material)
    material.title = title
    material.content = content
    material.due_at = due_at
    material.status = "pending"
    db.commit()
    db.refresh(material)
    return material


def _sync_course_items(
    db: Session,
    access_token: str,
    student_id: uuid.UUID,
    course_id: uuid.UUID,
    classroom_course_id: str,
    on_item: Optional[Callable[[bool], None]] = None,
) -> tuple[int, int]:
    """Ingest a course's items. Returns (synced, failed).

    Each item is independent: an unreadable attachment (encrypted PDF, corrupt
    file, Drive permission error) is logged and skipped, not fatal.
    """
    synced = failed = 0
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
                material = _get_or_create_material(
                    db, student_id, course_id,
                    external_id=item_id,
                    title=item.get("title") or f"{kind} sans titre",
                    content=text,
                    due_at=classroom_client.due_datetime(item) if kind == "courseWork" else None,
                )
                ingest_material(db, material)
            except Exception as exc:  # noqa: BLE001 - one bad item must not stop the sync
                db.rollback()  # keep the session usable for the next item
                failed += 1
                logger.warning("Skipping Classroom %s item %s (course=%s): %s: %s",
                               kind, item_id, course_id, type(exc).__name__, exc)
                if on_item:
                    on_item(False)
                continue
            synced += 1
            if on_item:
                on_item(True)
    return synced, failed


def sync_student_classroom(
    db: Session,
    student,
    account,
    on_progress: Optional[Callable[[int, int, int], None]] = None,
) -> dict[str, Any]:
    """Full sync for one student. ``on_progress(courses, synced, failed)`` is
    called as items and courses complete."""
    access_token = get_valid_access_token(db, account)
    totals = {"courses_synced": 0, "materials_synced": 0, "materials_failed": 0}

    def report():
        if on_progress:
            on_progress(totals["courses_synced"], totals["materials_synced"], totals["materials_failed"])

    def on_item(ok: bool):
        totals["materials_synced" if ok else "materials_failed"] += 1
        report()

    for classroom_course in classroom_client.list_courses(access_token):
        course, _enrollment = _get_or_create_course(db, student.id, classroom_course)
        _sync_course_items(db, access_token, student.id, course.id, classroom_course["id"], on_item=on_item)
        totals["courses_synced"] += 1
        report()

    account.last_synced_at = time.time()
    db.commit()
    return totals
