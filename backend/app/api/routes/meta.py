"""Small read-only endpoints the app shell needs: programmes, notifications,
onboarding status, and the source viewer behind citation links."""
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.models import Course, CourseMaterial, Department, DocumentChunk, Program, Student
from app.services import academic_calendar

router = APIRouter(tags=["Meta"])

NOTIFY_DAYS_AHEAD = 14


@router.get("/onboarding/status")
def onboarding_status(current_user: Student = Depends(get_current_user)):
    return {
        "onboarding_completed": current_user.onboarding_completed,
        "student_status": current_user.student_status,
        "academic_year": current_user.academic_year,
    }


@router.get("/programs")
def list_programs(db: Session = Depends(get_db)):
    """FSB programmes grouped by department (for onboarding and the profile)."""
    rows = (
        db.query(Program, Department.name)
        .outerjoin(Department, Department.id == Program.department_id)
        .order_by(Department.name, Program.level, Program.name)
        .all()
    )
    return [
        {"id": program.id, "name": program.name, "level": program.level, "department": department}
        for program, department in rows
    ]


@router.get("/notifications")
def notifications(db: Session = Depends(get_db), current_user: Student = Depends(get_current_user)):
    """Upcoming Classroom due dates and academic-calendar dates, soonest first."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    horizon = now + timedelta(days=NOTIFY_DAYS_AHEAD)
    items = [
        {
            "id": f"due-{material.id}",
            "kind": "deadline",
            "title": material.title,
            "detail": course_name,
            "date": material.due_at,
            "course_id": material.course_id,
        }
        for material, course_name in (
            db.query(CourseMaterial, Course.name)
            .join(Course, Course.id == CourseMaterial.course_id)
            .filter(
                CourseMaterial.student_id == current_user.id,
                CourseMaterial.due_at.isnot(None),
                CourseMaterial.due_at >= now,
                CourseMaterial.due_at <= horizon,
            )
        )
    ]
    today = date.today()
    items += [
        {
            "id": f"cal-{day.isoformat()}",
            "kind": "calendar",
            "title": label,
            "detail": academic_calendar.SOURCE,
            "date": datetime.combine(day, datetime.min.time()),
            "course_id": None,
        }
        for day, label in academic_calendar.EVENTS
        if today <= day <= today + timedelta(days=NOTIFY_DAYS_AHEAD)
    ]
    return sorted(items, key=lambda item: item["date"])


@router.get("/sources")
def source_excerpt(
    document: str = Query(..., max_length=300),
    page: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: Student = Depends(get_current_user),
):
    """The passages behind a citation ``[document, p.X]``: global knowledge-base
    chunks, plus the student's own course materials (never anyone else's)."""
    rows = (
        db.query(DocumentChunk.text, DocumentChunk.title, DocumentChunk.source, DocumentChunk.page)
        .filter(
            or_(DocumentChunk.title == document, DocumentChunk.source == document),
            DocumentChunk.page == page,
            or_(DocumentChunk.student_id.is_(None), DocumentChunk.student_id == current_user.id),
        )
        .limit(3)
        .all()
    )
    return {
        "document": document,
        "page": page,
        "passages": [{"text": r.text, "source": r.source} for r in rows],
    }
