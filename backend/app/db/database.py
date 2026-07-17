from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_schema():
    if engine.dialect.name != "postgresql":
        return

    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    with engine.begin() as connection:
        if "students" in table_names:
            student_columns = {column["name"] for column in inspector.get_columns("students")}

            if "role" not in student_columns:
                connection.execute(text("ALTER TABLE students ADD COLUMN role VARCHAR DEFAULT 'student'"))
                connection.execute(text("UPDATE students SET role = 'student' WHERE role IS NULL"))

            if "interests" not in student_columns:
                connection.execute(text("ALTER TABLE students ADD COLUMN interests JSONB"))
                connection.execute(text("UPDATE students SET interests = '[]'::jsonb WHERE interests IS NULL"))

            if "goals" not in student_columns:
                connection.execute(text("ALTER TABLE students ADD COLUMN goals JSONB"))
                connection.execute(text("UPDATE students SET goals = '[]'::jsonb WHERE goals IS NULL"))

            if "academic_year" in student_columns:
                connection.execute(text("ALTER TABLE students ALTER COLUMN academic_year TYPE VARCHAR USING academic_year::text"))

        if "document_chunks" in table_names:
            chunk_columns = {column["name"] for column in inspector.get_columns("document_chunks")}

            if "chunk_id" not in chunk_columns:
                connection.execute(text("ALTER TABLE document_chunks ADD COLUMN chunk_id UUID"))
                if "id" in chunk_columns:
                    connection.execute(text("UPDATE document_chunks SET chunk_id = id WHERE chunk_id IS NULL"))

            if "text" not in chunk_columns:
                connection.execute(text("ALTER TABLE document_chunks ADD COLUMN text TEXT"))
            if "title" not in chunk_columns:
                connection.execute(text("ALTER TABLE document_chunks ADD COLUMN title VARCHAR"))
            if "source" not in chunk_columns:
                connection.execute(text("ALTER TABLE document_chunks ADD COLUMN source VARCHAR"))
            if "page" not in chunk_columns:
                connection.execute(text("ALTER TABLE document_chunks ADD COLUMN page INTEGER"))
            if "category" not in chunk_columns:
                connection.execute(text("ALTER TABLE document_chunks ADD COLUMN category VARCHAR"))
            if "embedding" not in chunk_columns:
                connection.execute(text("ALTER TABLE document_chunks ADD COLUMN embedding JSONB"))
            if "document_id" in chunk_columns:
                connection.execute(text("ALTER TABLE document_chunks ALTER COLUMN document_id DROP NOT NULL"))
            if "student_id" not in chunk_columns:
                connection.execute(text("ALTER TABLE document_chunks ADD COLUMN student_id UUID"))
            if "course_id" not in chunk_columns:
                connection.execute(text("ALTER TABLE document_chunks ADD COLUMN course_id UUID"))
            if "material_id" not in chunk_columns:
                connection.execute(text("ALTER TABLE document_chunks ADD COLUMN material_id UUID"))
            connection.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_document_chunks_student_course "
                "ON document_chunks (student_id, course_id)"
            ))

        if "courses" in table_names:
            course_columns = {column["name"] for column in inspector.get_columns("courses")}
            if "code" not in course_columns:
                connection.execute(text("ALTER TABLE courses ADD COLUMN code VARCHAR"))
            if "description" not in course_columns:
                connection.execute(text("ALTER TABLE courses ADD COLUMN description TEXT"))
            if "source" not in course_columns:
                connection.execute(text("ALTER TABLE courses ADD COLUMN source VARCHAR DEFAULT 'manual'"))
                connection.execute(text("UPDATE courses SET source = 'manual' WHERE source IS NULL"))
            if "external_id" not in course_columns:
                connection.execute(text("ALTER TABLE courses ADD COLUMN external_id VARCHAR"))

        if "course_materials" in table_names:
            material_columns = {column["name"] for column in inspector.get_columns("course_materials")}
            if "original_filename" not in material_columns:
                connection.execute(text("ALTER TABLE course_materials ADD COLUMN original_filename VARCHAR"))