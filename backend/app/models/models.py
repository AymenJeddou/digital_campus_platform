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

class Document(Base):
    __tablename__ = "documents"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String)
    content = Column(Text, nullable=True)
    file_path = Column(String, nullable=True) # Allowed null for old documents
    uploaded_by_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=True)
    is_ingested = Column(Boolean, default=False)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    uploaded_by = relationship("Student")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    chunk_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"))
    text = Column(Text)
    title = Column(String)
    source = Column(String)
    page = Column(Integer)
    category = Column(String)
    embedding = Column(Vector(768) if Vector else JSON)

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
    citations = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    session = relationship("ChatSession", back_populates="messages")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"))
    action = Column(String)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class RevokedToken(Base):
    __tablename__ = "revoked_tokens"
    id = Column(Integer, primary_key=True, autoincrement=True)
    jti = Column(String, unique=True, nullable=False)
    revoked_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Feedback(Base):
    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_message_id = Column(UUID(as_uuid=True), ForeignKey("chat_messages.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(String, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    chat_message = relationship("ChatMessage")
    user = relationship("Student")

class GoogleClassroomToken(Base):
    __tablename__ = "google_classroom_tokens"
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), unique=True, nullable=False)
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    scope = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    student = relationship("Student")