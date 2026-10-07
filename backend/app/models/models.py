from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey, Float, JSON, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.database import Base
import uuid
from datetime import datetime, timezone

try:
    from pgvector.sqlalchemy import Vector
except ImportError:  # pragma: no cover - optional dependency for PostgreSQL deployments
    Vector = None


def _now():
    return datetime.now(timezone.utc)


class Student(Base):
    __tablename__ = "students"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    role = Column(String, default="student")  # "student" | "admin" (set in the DB only)
    student_status = Column(String, default="prospective")  # prospective | enrolled | alumni
    academic_year = Column(String)
    program_id = Column(UUID(as_uuid=True), ForeignKey("programs.id"), nullable=True)
    bac_type = Column(String)
    bac_score = Column(Float)
    interests = Column(JSON, default=list)
    goals = Column(JSON, default=list)
    enrollment_date = Column(DateTime, default=_now)
    onboarding_completed = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)

    program = relationship("Program")


class Department(Base):
    __tablename__ = "departments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)


class Program(Base):
    """An FSB degree programme (licence or master), seeded by migration from the
    official offer published on fsb.rnu.tn."""
    __tablename__ = "programs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    level = Column(String, nullable=True)  # "licence" | "master_recherche" | "master_pro"
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"))

    department = relationship("Department")


class Course(Base):
    __tablename__ = "courses"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    program_id = Column(UUID(as_uuid=True), ForeignKey("programs.id"))
    code = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    # "manual" courses form the shared catalog. "google_classroom" courses are
    # private to the student whose Classroom they were synced from and are
    # never listed in the catalog.
    source = Column(String, default="manual")
    external_id = Column(String, nullable=True)  # Classroom course id


class Document(Base):
    __tablename__ = "documents"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String)
    content = Column(Text, nullable=True)
    file_path = Column(String, nullable=True)  # NULL for documents from before uploads existed
    uploaded_by_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=True)
    is_ingested = Column(Boolean, default=False)
    uploaded_at = Column(DateTime, default=_now)

    uploaded_by = relationship("Student")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    chunk_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True)
    text = Column(Text)
    title = Column(String)
    source = Column(String)
    page = Column(Integer)
    category = Column(String)
    embedding = Column(Vector(768) if Vector else JSON)
    # Course-scoping (nullable): NULL/NULL means a regular knowledge-base chunk,
    # visible to everyone. When both are set, the chunk is a course-material
    # chunk that must only ever be retrieved for that exact student+course.
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=True)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=True)
    material_id = Column(UUID(as_uuid=True), ForeignKey("course_materials.id"), nullable=True)


class StudentCourse(Base):
    """A student's enrollment in a course (manual, or synced from Google Classroom)."""
    __tablename__ = "student_courses"
    __table_args__ = (UniqueConstraint("student_id", "course_id", name="uq_student_course"),)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False)
    source = Column(String, default="manual")  # "manual" | "google_classroom"
    external_id = Column(String, nullable=True)  # Classroom course id, once synced
    enrolled_at = Column(DateTime, default=_now)


class CourseMaterial(Base):
    """A piece of course content belonging to one student's view of one course."""
    __tablename__ = "course_materials"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text)  # raw text (typed manually, or extracted from an upload)
    source = Column(String, default="manual")  # "manual" | "upload" | "google_classroom"
    external_id = Column(String, nullable=True)
    original_filename = Column(String, nullable=True)  # "upload" source only
    due_at = Column(DateTime, nullable=True)  # Classroom coursework due date, if any
    status = Column(String, default="pending")  # pending | ingested | error
    chunk_count = Column(Integer, default=0)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)


class GoogleClassroomAccount(Base):
    """One row per student who has connected Google Classroom. Tokens are
    stored encrypted (see app/services/token_crypto.py). Sync progress lives
    here too, so it survives restarts and is shared across workers."""
    __tablename__ = "google_classroom_accounts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False, unique=True)
    access_token = Column(String, nullable=False)  # encrypted
    refresh_token = Column(String, nullable=False)  # encrypted
    token_expires_at = Column(Float, nullable=False)  # unix timestamp
    scope = Column(String, nullable=True)
    connected_at = Column(DateTime, default=_now)
    last_synced_at = Column(Float, nullable=True)  # unix timestamp
    sync_status = Column(String, default="idle")  # idle | running | success | error
    sync_started_at = Column(Float, nullable=True)
    sync_courses_synced = Column(Integer, default=0)
    sync_materials_synced = Column(Integer, default=0)
    sync_materials_failed = Column(Integer, default=0)
    sync_error = Column(String, nullable=True)


class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"))
    title = Column(String, nullable=True)  # first question, renamable
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now)
    messages = relationship("ChatMessage", back_populates="session")


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"))
    role = Column(String)
    content = Column(Text)
    citations = Column(JSON, nullable=True)
    # Groundedness verdict for assistant answers: False = the judge found the
    # sources don't fully support it (shown as a warning). NULL = not graded.
    grounded = Column(Boolean, nullable=True)
    created_at = Column(DateTime, default=_now)
    session = relationship("ChatSession", back_populates="messages")


class RevokedToken(Base):
    __tablename__ = "revoked_tokens"
    id = Column(Integer, primary_key=True, autoincrement=True)
    jti = Column(String, unique=True, nullable=False)
    revoked_at = Column(DateTime, default=_now)


class Feedback(Base):
    __tablename__ = "feedback"
    __table_args__ = (UniqueConstraint("chat_message_id", "user_id", name="uq_feedback_message_user"),)
    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_message_id = Column(UUID(as_uuid=True), ForeignKey("chat_messages.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1 = helpful, 0 = not helpful
    comment = Column(String, nullable=True)
    timestamp = Column(DateTime, default=_now)

    chat_message = relationship("ChatMessage")
    user = relationship("Student")
