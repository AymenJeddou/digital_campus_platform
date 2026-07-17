from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey, Float, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.database import Base
import uuid
from datetime import datetime, timezone

try:
    from pgvector.sqlalchemy import Vector
except ImportError:  # pragma: no cover - optional dependency for PostgreSQL deployments
    Vector = None

class Student(Base):
    __tablename__ = "students"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    role = Column(String, default="student")
    student_status = Column(String, default="prospective")
    academic_year = Column(String)
    bac_type = Column(String)
    bac_score = Column(Float)
    interests = Column(JSON, default=list)
    goals = Column(JSON, default=list)
    enrollment_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    onboarding_completed = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)

class Program(Base):
    __tablename__ = "programs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"))

class Department(Base):
    __tablename__ = "departments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)

class Course(Base):
    __tablename__ = "courses"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    program_id = Column(UUID(as_uuid=True), ForeignKey("programs.id"))
    code = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    # Set when this course was created from a Google Classroom sync, so a
    # given Classroom course maps to exactly one Course row shared by every
    # student enrolled in it via Classroom (see StudentCourse.source below).
    source = Column(String, default="manual")  # "manual" | "google_classroom"
    external_id = Column(String, nullable=True)  # Classroom course id

class Document(Base):
    __tablename__ = "documents"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String)
    content = Column(Text)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

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
    """A student's enrollment in a course (manual path, or synced later from
    an external source such as Google Classroom)."""
    __tablename__ = "student_courses"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False)
    source = Column(String, default="manual")  # "manual" | "google_classroom"
    external_id = Column(String, nullable=True)  # Classroom course id, once synced
    enrolled_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class CourseMaterial(Base):
    """A piece of course content (uploaded manually, or later pulled in from
    Google Classroom) belonging to one student's view of one course."""
    __tablename__ = "course_materials"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text)  # raw text content (typed manually, or extracted from an upload)
    source = Column(String, default="manual")  # "manual" | "upload" | "google_classroom"
    external_id = Column(String, nullable=True)
    # Original filename for the "upload" source (PDF/DOCX/TXT/MD) — kept for
    # display and re-download context. NULL for "manual" and "google_classroom".
    original_filename = Column(String, nullable=True)
    status = Column(String, default="pending")  # pending | ingested | error
    chunk_count = Column(Integer, default=0)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class GoogleClassroomAccount(Base):
    """One row per student who has connected Google Classroom.

    Tokens are stored encrypted (see `app/services/token_crypto.py`) with a
    key derived from the app's existing SECRET_KEY by default. The blueprint
    assigns hardening this ("secure token storage") to Role 4 (6.4); swapping
    in a dedicated, rotated encryption key is a one-line change there.
    """
    __tablename__ = "google_classroom_accounts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False, unique=True)
    access_token = Column(String, nullable=False)  # encrypted
    refresh_token = Column(String, nullable=False)  # encrypted
    token_expires_at = Column(Float, nullable=False)  # unix timestamp
    scope = Column(String, nullable=True)
    connected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_synced_at = Column(Float, nullable=True)  # unix timestamp


class AdmissionScore(Base):
    __tablename__ = "admission_scores"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"))
    score = Column(Float)

class Recommendation(Base):
    __tablename__ = "recommendations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"))
    content = Column(Text)

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    messages = relationship("ChatMessage", back_populates="session")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"))
    role = Column(String)
    content = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    session = relationship("ChatSession", back_populates="messages")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"))
    action = Column(String)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))