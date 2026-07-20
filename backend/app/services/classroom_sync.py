"""Google Classroom sync: turns a connected student's Classroom courses,
coursework, courseWorkMaterials, and announcements into local `Course` /
`StudentCourse` / `CourseMaterial` rows, then reuses the existing
`course_ingestion.ingest_material` to chunk + embed them — the same path
manual uploads go through, so retrieval and `/chat` course-scoping need no
special-casing for the Classroom source.
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.services import classroom_client
from app.services.course_ingestion import ingest_material
from app.services.token_crypto import decrypt_token, encrypt_token

logger = logging.getLogger(__name__)

TOKEN_REFRESH_SKEW_SECONDS = 60


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


def _sync_course_items(db: Session, access_token: str, student_id: uuid.UUID, course_id: uuid.UUID, classroom_course_id: str) -> int:
    materials_synced = 0

    items: list[tuple[str, str]] = []  # (external_id, kind) just for logging clarity
    for kind, fetcher in (
        ("courseWork", classroom_client.list_coursework),
        ("courseWorkMaterial", classroom_client.list_coursework_materials),
        ("announcement", classroom_client.list_announcements),
    ):
        for item in fetcher(access_token, classroom_course_id):
            text = classroom_client.item_to_material_text(access_token, item)
            if not text.strip():
                continue
            title = item.get("title") or f"{kind} sans titre"
            material = _get_or_create_material(
                db, student_id, course_id,
                external_id=item["id"],
                title=title,
                content=text,
            )
            ingest_material(db, material)
            materials_synced += 1
            items.append((item["id"], kind))

    logger.info("Synced %d materials for course=%s student=%s", materials_synced, course_id, student_id)
    return materials_synced


def sync_student_classroom(db: Session, student, account) -> dict[str, Any]:
    """Full sync for one student: courses + their coursework/materials/announcements."""
    access_token = get_valid_access_token(db, account)

    courses_synced = 0
    materials_synced = 0
    synced_courses: list[dict[str, Any]] = []

    for classroom_course in classroom_client.list_courses(access_token):
        course, _enrollment = _get_or_create_course(db, student.id, classroom_course)
        count = _sync_course_items(db, access_token, student.id, course.id, classroom_course["id"])
        courses_synced += 1
        materials_synced += count
        synced_courses.append({"id": course.id, "name": course.name, "materials_synced": count})

    account.last_synced_at = time.time()
    db.commit()

    return {
        "courses_synced": courses_synced,
        "materials_synced": materials_synced,
        "courses": synced_courses,
    }
