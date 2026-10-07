import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import jwt
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import RedirectResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.models import Course, CourseMaterial, GoogleClassroomAccount, Student, StudentCourse
from app.schemas.course import (
    ClassroomAuthorizeResponse,
    ClassroomConnectRequest,
    ClassroomStatusResponse,
    ClassroomSyncResponse,
    CourseCreateRequest,
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
from app.services.token_crypto import decrypt_token, encrypt_token

router = APIRouter(prefix="/courses", tags=["Courses"])

STATE_PURPOSE = "classroom_oauth"
STATE_TTL_MINUTES = 10

# A handout or slide export, not a textbook. Bounds upload + extraction time
# and memory (the file is read into memory once).
MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20 MB


def _require_enrollment(db: Session, student: Student, course_id: uuid.UUID) -> StudentCourse:
    enrollment = db.query(StudentCourse).filter(
        StudentCourse.student_id == student.id, StudentCourse.course_id == course_id
    ).first()
    if not enrollment:
        raise HTTPException(status_code=403, detail="You are not enrolled in this course")
    return enrollment


def _enrolled_response(course: Course, enrollment: StudentCourse, material_count: int = 0) -> EnrolledCourseResponse:
    return EnrolledCourseResponse(
        id=course.id,
        name=course.name,
        program_id=course.program_id,
        code=course.code,
        description=course.description,
        enrolled_at=enrollment.enrolled_at,
        source=enrollment.source,
        material_count=material_count,
    )


def _enroll(db: Session, student: Student, course: Course) -> EnrolledCourseResponse:
    if db.query(StudentCourse).filter(
        StudentCourse.student_id == student.id, StudentCourse.course_id == course.id
    ).first():
        raise HTTPException(status_code=409, detail="Already enrolled in this course")
    enrollment = StudentCourse(student_id=student.id, course_id=course.id, source="manual")
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return _enrolled_response(course, enrollment)


@router.get("", response_model=list[CourseResponse])
def list_courses(
    program_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    current_user: Student = Depends(get_current_user),
):
    """The shared course catalog. Courses synced from a student's Google
    Classroom are private to that student and never listed here."""
    query = db.query(Course).filter(Course.source == "manual")
    if program_id:
        query = query.filter(Course.program_id == program_id)
    return query.order_by(Course.name).all()


@router.post("", response_model=EnrolledCourseResponse, status_code=201)
def create_and_enroll(
    body: CourseCreateRequest,
    db: Session = Depends(get_db),
    current_user: Student = Depends(get_current_user),
):
    """Add a course by name and enrol in one step. Reuses the catalog course
    with the same name (case-insensitive, exact) instead of duplicating it."""
    name = " ".join(body.name.split())
    course = db.query(Course).filter(
        Course.source == "manual", func.lower(Course.name) == name.lower()
    ).first()
    if not course:
        course = Course(name=name, code=body.code, description=body.description, source="manual")
        db.add(course)
        db.commit()
        db.refresh(course)
    return _enroll(db, current_user, course)


@router.get("/mine", response_model=list[EnrolledCourseResponse])
def list_my_courses(db: Session = Depends(get_db), current_user: Student = Depends(get_current_user)):
    """Courses the current student is enrolled in, with their material count."""
    counts = (
        db.query(CourseMaterial.course_id, func.count(CourseMaterial.id).label("n"))
        .filter(CourseMaterial.student_id == current_user.id)
        .group_by(CourseMaterial.course_id)
        .subquery()
    )
    rows = (
        db.query(StudentCourse, Course, func.coalesce(counts.c.n, 0))
        .join(Course, Course.id == StudentCourse.course_id)
        .outerjoin(counts, counts.c.course_id == Course.id)
        .filter(StudentCourse.student_id == current_user.id)
        .order_by(StudentCourse.enrolled_at.desc())
        .all()
    )
    return [_enrolled_response(course, enrollment, count) for enrollment, course, count in rows]


@router.post("/enroll", response_model=EnrolledCourseResponse, status_code=201)
def enroll_in_course(
    body: CourseEnrollRequest,
    db: Session = Depends(get_db),
    current_user: Student = Depends(get_current_user),
):
    """Enrol in an existing catalog course."""
    course = db.query(Course).filter(Course.id == body.course_id, Course.source == "manual").first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return _enroll(db, current_user, course)


@router.delete("/enroll/{course_id}", status_code=204)
def unenroll_from_course(
    course_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: Student = Depends(get_current_user),
):
    """Leave a course. The student's own materials for it (and their search
    chunks) go too, so nothing private is left behind."""
    enrollment = _require_enrollment(db, current_user, course_id)
    for material in db.query(CourseMaterial).filter(
        CourseMaterial.course_id == course_id, CourseMaterial.student_id == current_user.id
    ):
        delete_material_chunks(db, material.id, commit=False)
        db.delete(material)
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
        source=course.source or "manual",
        materials=materials,
    )


def _create_material(db: Session, student: Student, course_id: uuid.UUID, **fields) -> CourseMaterial:
    material = CourseMaterial(course_id=course_id, student_id=student.id, status="pending", **fields)
    db.add(material)
    db.commit()
    db.refresh(material)
    ingest_material(db, material)
    db.refresh(material)
    return material


@router.post("/{course_id}/materials", response_model=CourseMaterialResponse, status_code=201)
def add_course_material(
    course_id: uuid.UUID,
    body: CourseMaterialCreate,
    db: Session = Depends(get_db),
    current_user: Student = Depends(get_current_user),
):
    """Add typed / pasted text as course material."""
    _require_enrollment(db, current_user, course_id)
    return _create_material(db, current_user, course_id, title=body.title, content=body.content, source="manual")


# A plain `def`: extraction and embedding are CPU-bound, so FastAPI runs this
# in its worker threadpool instead of blocking the event loop.
@router.post("/{course_id}/materials/upload", response_model=CourseMaterialResponse, status_code=201)
def upload_course_material(
    course_id: uuid.UUID,
    file: UploadFile = File(...),
    title: str | None = Form(None, max_length=200),
    db: Session = Depends(get_db),
    current_user: Student = Depends(get_current_user),
):
    """Upload a PDF, DOCX, PPTX, TXT or MD file as course material. Its text is
    extracted server-side and goes through the same ingestion as typed text."""
    _require_enrollment(db, current_user, course_id)

    raw = file.file.read(MAX_UPLOAD_BYTES + 1)  # never read more than the limit
    if not raw:
        raise HTTPException(status_code=422, detail="The uploaded file is empty")
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"File too large — the limit is {MAX_UPLOAD_BYTES // 1_000_000} MB.")

    try:
        extracted_text = extract_text(file.filename, raw)
    except UnsupportedFileType as exc:
        raise HTTPException(status_code=415, detail=str(exc))
    except TextExtractionError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    return _create_material(
        db, current_user, course_id,
        title=(title or file.filename or "Document")[:200],
        content=extracted_text,
        source="upload",
        original_filename=file.filename,
    )


def _owned_material(db: Session, user: Student, course_id: uuid.UUID, material_id: uuid.UUID) -> CourseMaterial:
    material = db.query(CourseMaterial).filter(
        CourseMaterial.id == material_id,
        CourseMaterial.course_id == course_id,
        CourseMaterial.student_id == user.id,
    ).first()
    if not material:
        raise HTTPException(status_code=404, detail="Course material not found")
    return material


@router.post("/{course_id}/materials/{material_id}/refresh", response_model=CourseMaterialResponse)
def refresh_course_material(
    course_id: uuid.UUID,
    material_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: Student = Depends(get_current_user),
):
    """Re-chunk and re-embed a material."""
    material = _owned_material(db, current_user, course_id, material_id)
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
    material = _owned_material(db, current_user, course_id, material_id)
    delete_material_chunks(db, material.id, commit=False)
    db.delete(material)
    db.commit()


# --- Google Classroom integration -----------------------------------------
#
# Flow: the frontend asks /classroom/authorize for Google's consent URL (with a
# signed `state` naming the student). Google redirects the browser to
# /classroom/callback, which only forwards `code` + `state` to the frontend.
# The frontend then calls /classroom/connect WITH the student's bearer token,
# and the tokens are stored only if the state was issued to that same student.
# Binding the exchange to the logged-in browser is what stops an attacker from
# sending someone a consent link and having that person's Classroom attached
# to the attacker's account.

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


def _frontend_redirect(**params) -> RedirectResponse:
    return RedirectResponse(f"{settings.FRONTEND_URL}/courses?{urlencode(params)}")


@router.post("/classroom/authorize", response_model=ClassroomAuthorizeResponse)
def classroom_authorize(current_user: Student = Depends(get_current_user)):
    """Returns the Google consent-screen URL for the frontend to redirect to."""
    try:
        url = classroom_client.build_authorization_url(_sign_state(current_user.id))
    except classroom_client.ClassroomAPIError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return ClassroomAuthorizeResponse(authorization_url=url)


@router.get("/classroom/callback", include_in_schema=False)
def classroom_callback(code: str | None = None, state: str | None = None, error: str | None = None):
    """Public redirect target for Google's consent screen. Stores nothing:
    hands code + state to the frontend, which completes /classroom/connect."""
    if error or not code or not state:
        return _frontend_redirect(classroom="error")
    try:
        _verify_state(state)
    except HTTPException:
        return _frontend_redirect(classroom="error")
    return _frontend_redirect(classroom_code=code, classroom_state=state)


@router.post("/classroom/connect", response_model=ClassroomStatusResponse)
def classroom_connect(
    body: ClassroomConnectRequest,
    db: Session = Depends(get_db),
    current_user: Student = Depends(get_current_user),
):
    if _verify_state(body.state) != current_user.id:
        raise HTTPException(status_code=403, detail="This Classroom authorization was started by another account")
    try:
        token_set = classroom_client.exchange_code_for_tokens(body.code)
    except classroom_client.ClassroomAPIError:
        raise HTTPException(status_code=502, detail="Google refused the authorization. Please try again.")
    if not token_set.refresh_token:
        # We always send prompt=consent, so this is a defensive fallback.
        raise HTTPException(status_code=409, detail="Google did not grant offline access. Please try again.")

    account = _get_account(db, current_user.id) or GoogleClassroomAccount(student_id=current_user.id)
    account.access_token = encrypt_token(token_set.access_token)
    account.refresh_token = encrypt_token(token_set.refresh_token)
    account.token_expires_at = token_set.expires_at
    account.scope = token_set.scope
    db.add(account)
    db.commit()
    return classroom_status(db, current_user)


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
        sync_status=classroom_sync.effective_status(account),
        sync_courses_synced=account.sync_courses_synced or 0,
        sync_materials_synced=account.sync_materials_synced or 0,
        sync_materials_failed=account.sync_materials_failed or 0,
        sync_error=account.sync_error,
    )


@router.post("/classroom/sync", response_model=ClassroomSyncResponse, status_code=202)
def classroom_sync_now(db: Session = Depends(get_db), current_user: Student = Depends(get_current_user)):
    """Start a background sync of the student's Classroom courses, coursework,
    materials and announcements; returns immediately. Poll /classroom/status."""
    account = _get_account(db, current_user.id)
    if not account:
        raise HTTPException(status_code=400, detail="Google Classroom is not connected for this student")
    classroom_sync.start_sync(db, account)
    db.refresh(account)
    return ClassroomSyncResponse(
        status=classroom_sync.effective_status(account),
        courses_synced=account.sync_courses_synced or 0,
        materials_synced=account.sync_materials_synced or 0,
        materials_failed=account.sync_materials_failed or 0,
    )


@router.delete("/classroom", status_code=204)
def classroom_disconnect(db: Session = Depends(get_db), current_user: Student = Depends(get_current_user)):
    """Disconnect: revoke the grant at Google and forget the tokens. Synced
    courses stay (unenrol from them separately if wanted)."""
    account = _get_account(db, current_user.id)
    if not account:
        raise HTTPException(status_code=404, detail="Google Classroom is not connected for this student")
    try:
        classroom_client.revoke_token(decrypt_token(account.refresh_token))
    except Exception:  # best-effort: forgetting the tokens locally still disconnects
        pass
    db.delete(account)
    db.commit()
