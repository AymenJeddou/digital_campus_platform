import uuid
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.models import Course, CourseMaterial, DocumentChunk, GoogleClassroomAccount, Student, StudentCourse
from app.schemas.course import (
    ClassroomAuthorizeResponse,
    ClassroomStatusResponse,
    ClassroomSyncResponse,
    CourseDetailResponse,
    CourseEnrollRequest,
    CourseMaterialCreate,
    CourseMaterialResponse,
    CourseResponse,
    EnrolledCourseResponse,
)
from app.services import classroom_client, classroom_sync
from app.services.course_ingestion import delete_material_chunks, ingest_material
from app.services.text_extraction import TextExtractionError, UnsupportedFileType, extract_text
from app.services.token_crypto import encrypt_token

router = APIRouter(prefix="/courses", tags=["Courses"])

STATE_PURPOSE = "classroom_oauth"
STATE_TTL_MINUTES = 10

# Same order of magnitude as a handout or a slide export; large enough for
# real course materials, small enough to keep upload + extraction fast and
# to bound worst-case memory use (the whole file is read into memory once).
MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20 MB


def _get_enrollment(db: Session, student_id: uuid.UUID, course_id: uuid.UUID) -> StudentCourse | None:
    return (
        db.query(StudentCourse)
        .filter(StudentCourse.student_id == student_id, StudentCourse.course_id == course_id)
        .first()
    )


def _require_enrollment(db: Session, student: Student, course_id: uuid.UUID) -> StudentCourse:
    enrollment = _get_enrollment(db, student.id, course_id)
    if not enrollment:
        raise HTTPException(status_code=403, detail="You are not enrolled in this course")
    return enrollment


@router.get("", response_model=list[CourseResponse])
def list_courses(
    program_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    current_user: Student = Depends(get_current_user),
):
    """Course catalog — every course a student could enroll in."""
    query = db.query(Course)
    if program_id:
        query = query.filter(Course.program_id == program_id)
    return query.all()


@router.get("/mine", response_model=list[EnrolledCourseResponse])
def list_my_courses(db: Session = Depends(get_db), current_user: Student = Depends(get_current_user)):
    """Courses the current student is enrolled in, with their material count."""
    enrollments = db.query(StudentCourse).filter(StudentCourse.student_id == current_user.id).all()
    results = []
    for enrollment in enrollments:
        course = db.query(Course).filter(Course.id == enrollment.course_id).first()
        if not course:
            continue
        material_count = (
            db.query(CourseMaterial)
            .filter(
                CourseMaterial.course_id == course.id,
                CourseMaterial.student_id == current_user.id,
            )
            .count()
        )
        results.append(EnrolledCourseResponse(
            id=course.id,
            name=course.name,
            program_id=course.program_id,
            code=course.code,
            description=course.description,
            enrolled_at=enrollment.enrolled_at,
            source=enrollment.source,
            material_count=material_count,
        ))
    return results


@router.post("/enroll", response_model=EnrolledCourseResponse, status_code=201)
def enroll_in_course(
    body: CourseEnrollRequest,
    db: Session = Depends(get_db),
    current_user: Student = Depends(get_current_user),
):
    """Manual enrollment path — always available, independent of Google Classroom
    authorization (see Role 2 handoff)."""
    course = db.query(Course).filter(Course.id == body.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    existing = _get_enrollment(db, current_user.id, course.id)
    if existing:
        raise HTTPException(status_code=409, detail="Already enrolled in this course")

    enrollment = StudentCourse(student_id=current_user.id, course_id=course.id, source="manual")
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)

    return EnrolledCourseResponse(
        id=course.id,
        name=course.name,
        program_id=course.program_id,
        code=course.code,
        description=course.description,
        enrolled_at=enrollment.enrolled_at,
        source=enrollment.source,
        material_count=0,
    )


@router.delete("/enroll/{course_id}", status_code=204)
def unenroll_from_course(
    course_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: Student = Depends(get_current_user),
):
    enrollment = _require_enrollment(db, current_user, course_id)
    db.delete(enrollment)
    db.commit()


@router.get("/{course_id}", response_model=CourseDetailResponse)
def get_course(
    course_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: Student = Depends(get_current_user),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    _require_enrollment(db, current_user, course_id)

    materials = (
        db.query(CourseMaterial)
        .filter(CourseMaterial.course_id == course_id, CourseMaterial.student_id == current_user.id)
        .order_by(CourseMaterial.created_at.desc())
        .all()
    )
    return CourseDetailResponse(
        id=course.id,
        name=course.name,
        program_id=course.program_id,
        code=course.code,
        description=course.description,
        materials=materials,
    )


@router.post("/{course_id}/materials", response_model=CourseMaterialResponse, status_code=201)
def add_course_material(
    course_id: uuid.UUID,
    body: CourseMaterialCreate,
    db: Session = Depends(get_db),
    current_user: Student = Depends(get_current_user),
):
    """Manual course-content upload — the path available today, ahead of the
    Google Classroom integration which needs external authorization."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    _require_enrollment(db, current_user, course_id)

    material = CourseMaterial(
        course_id=course_id,
        student_id=current_user.id,
        title=body.title,
        content=body.content,
        source="manual",
        status="pending",
    )
    db.add(material)
    db.commit()
    db.refresh(material)

    ingest_material(db, material)
    db.refresh(material)
    return material


@router.post("/{course_id}/materials/upload", response_model=CourseMaterialResponse, status_code=201)
async def upload_course_material(
    course_id: uuid.UUID,
    file: UploadFile = File(...),
    title: str | None = Form(None),
    db: Session = Depends(get_db),
    current_user: Student = Depends(get_current_user),
):
    """Upload a real file (PDF, DOCX, TXT, or MD) as course material — the
    file-upload counterpart to `add_course_material` above, which only takes
    already-typed text. Text is extracted server-side and then run through
    the same `ingest_material` pipeline, so an uploaded PDF is chunked,
    embedded, and retrievable exactly like a manually-typed material."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    _require_enrollment(db, current_user, course_id)

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=422, detail="The uploaded file is empty")
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({len(raw) / 1_000_000:.1f} MB) — the limit is "
            f"{MAX_UPLOAD_BYTES // 1_000_000} MB.",
        )

    try:
        extracted_text = extract_text(file.filename, raw)
    except UnsupportedFileType as exc:
        raise HTTPException(status_code=415, detail=str(exc))
    except TextExtractionError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    material = CourseMaterial(
        course_id=course_id,
        student_id=current_user.id,
        title=title or file.filename,
        content=extracted_text,
        source="upload",
        original_filename=file.filename,
        status="pending",
    )
    db.add(material)
    db.commit()
    db.refresh(material)

    ingest_material(db, material)
    db.refresh(material)
    return material


@router.post("/{course_id}/materials/{material_id}/refresh", response_model=CourseMaterialResponse)
def refresh_course_material(
    course_id: uuid.UUID,
    material_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: Student = Depends(get_current_user),
):
    """Re-chunk and re-embed a material — e.g. after its content changes, or
    once it is synced from an external source."""
    material = (
        db.query(CourseMaterial)
        .filter(
            CourseMaterial.id == material_id,
            CourseMaterial.course_id == course_id,
            CourseMaterial.student_id == current_user.id,
        )
        .first()
    )
    if not material:
        raise HTTPException(status_code=404, detail="Course material not found")

    ingest_material(db, material)
    db.refresh(material)
    return material


@router.delete("/{course_id}/materials/{material_id}", status_code=204)
def delete_course_material(
    course_id: uuid.UUID,
    material_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: Student = Depends(get_current_user),
):
    material = (
        db.query(CourseMaterial)
        .filter(
            CourseMaterial.id == material_id,
            CourseMaterial.course_id == course_id,
            CourseMaterial.student_id == current_user.id,
        )
        .first()
    )
    if not material:
        raise HTTPException(status_code=404, detail="Course material not found")

    delete_material_chunks(db, material.id)
    db.delete(material)
    db.commit()


# --- Google Classroom integration -----------------------------------------
#
# Manual enrollment/upload above is always available; this section adds the
# target automated source per the blueprint (6.2). Because the OAuth
# callback is a browser redirect from Google — it carries no bearer token —
# it is exempted from the app-wide auth-required middleware in `main.py`
# and instead authenticates the student via the signed `state` value.

def _sign_state(student_id: uuid.UUID) -> str:
    payload = {
        "sub": str(student_id),
        "purpose": STATE_PURPOSE,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=STATE_TTL_MINUTES),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def _verify_state(state: str) -> uuid.UUID:
    try:
        payload = jwt.decode(state, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired Classroom authorization state")
    if payload.get("purpose") != STATE_PURPOSE:
        raise HTTPException(status_code=400, detail="Invalid Classroom authorization state")
    return uuid.UUID(payload["sub"])


def _get_account(db: Session, student_id: uuid.UUID) -> GoogleClassroomAccount | None:
    return db.query(GoogleClassroomAccount).filter(GoogleClassroomAccount.student_id == student_id).first()


@router.post("/classroom/authorize", response_model=ClassroomAuthorizeResponse)
def classroom_authorize(current_user: Student = Depends(get_current_user)):
    """Returns the Google consent-screen URL. The frontend should redirect
    the browser to `authorization_url`; Google redirects back to the public
    `/courses/classroom/callback` endpoint below once the student consents."""
    state = _sign_state(current_user.id)
    try:
        url = classroom_client.build_authorization_url(state)
    except classroom_client.ClassroomAPIError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return ClassroomAuthorizeResponse(authorization_url=url)


@router.get("/classroom/callback", include_in_schema=False)
def classroom_callback(code: str | None = None, state: str | None = None, error: str | None = None, db: Session = Depends(get_db)):
    """Public redirect target for Google's OAuth consent screen. Not called
    directly by the frontend app — see `classroom_authorize` above."""
    frontend_url = settings.FRONTEND_URL

    if error or not code or not state:
        return RedirectResponse(f"{frontend_url}/courses?classroom=error")

    try:
        student_id = _verify_state(state)
    except HTTPException:
        return RedirectResponse(f"{frontend_url}/courses?classroom=error")

    try:
        token_set = classroom_client.exchange_code_for_tokens(code)
    except classroom_client.ClassroomAPIError:
        return RedirectResponse(f"{frontend_url}/courses?classroom=error")

    if not token_set.refresh_token:
        # Happens if the student had already granted consent without
        # `prompt=consent` in an earlier attempt; ask them to retry, since we
        # only get a refresh_token on first consent (or with prompt=consent,
        # which we always send — this is a defensive fallback).
        return RedirectResponse(f"{frontend_url}/courses?classroom=retry")

    account = _get_account(db, student_id)
    if not account:
        account = GoogleClassroomAccount(student_id=student_id)
        db.add(account)

    account.access_token = encrypt_token(token_set.access_token)
    account.refresh_token = encrypt_token(token_set.refresh_token)
    account.token_expires_at = token_set.expires_at
    account.scope = token_set.scope
    db.commit()

    return RedirectResponse(f"{frontend_url}/courses?classroom=connected")


@router.get("/classroom/status", response_model=ClassroomStatusResponse)
def classroom_status(db: Session = Depends(get_db), current_user: Student = Depends(get_current_user)):
    account = _get_account(db, current_user.id)
    if not account:
        return ClassroomStatusResponse(connected=False)
    return ClassroomStatusResponse(
        connected=True,
        connected_at=account.connected_at,
        last_synced_at=(
            datetime.fromtimestamp(account.last_synced_at, tz=timezone.utc) if account.last_synced_at else None
        ),
    )


@router.post("/classroom/sync", response_model=ClassroomSyncResponse)
def classroom_sync_now(db: Session = Depends(get_db), current_user: Student = Depends(get_current_user)):
    """Pull the student's active Classroom courses, coursework,
    courseWorkMaterials, and announcements, and ingest them the same way a
    manual upload is ingested (see `course_ingestion.ingest_material`)."""
    account = _get_account(db, current_user.id)
    if not account:
        raise HTTPException(status_code=400, detail="Google Classroom is not connected for this student")

    try:
        result = classroom_sync.sync_student_classroom(db, current_user, account)
    except classroom_client.ClassroomAPIError as exc:
        raise HTTPException(status_code=502, detail=f"Google Classroom sync failed: {exc}")

    return ClassroomSyncResponse(**result)


@router.delete("/classroom", status_code=204)
def classroom_disconnect(db: Session = Depends(get_db), current_user: Student = Depends(get_current_user)):
    """Revoke the local connection. Existing synced courses/materials are
    left in place (same as unenrolling would need to be done separately) —
    this only stops future syncs."""
    account = _get_account(db, current_user.id)
    if not account:
        raise HTTPException(status_code=404, detail="Google Classroom is not connected for this student")
    db.delete(account)
    db.commit()
