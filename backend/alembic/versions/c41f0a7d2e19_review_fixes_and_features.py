"""review fixes and features

- chat: session titles, grounded flag on messages
- classroom: sync state persisted on the account, due dates on materials,
  Classroom courses marked private (kept out of the shared catalog)
- integrity: one enrollment per student/course, one feedback per user/message
- programmes: level + student.program_id, seeded with the FSB offer
- search: indexes for course scoping and French full-text
- drops the never-used admission_scores / recommendations / audit_logs tables

Revision ID: c41f0a7d2e19
Revises: bedd2ef53ea5
Create Date: 2026-10-07
"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "c41f0a7d2e19"
down_revision: Union[str, None] = "bedd2ef53ea5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Official offer (knowledge_base/orientation/web/fsb_licences.md and
# fsb_masteres_liste.md).
DEPARTMENTS = {
    "Physique": [
        ("licence", "Génie énergétique : Froid et climatisation"),
        ("licence", "Physique : Physique et énergie"),
        ("licence", "Physique-Chimie"),
        ("licence", "Physique des matériaux : Matériaux composites et avancés"),
        ("licence", "EEA : Automatique et informatique industrielle"),
        ("licence", "TIC : Communication et systèmes embarqués"),
        ("licence", "Physique : Physique des capteurs"),
        ("master_recherche", "Physique des matériaux et applications"),
        ("master_pro", "Électronique, Électrotechnique et Automatique (EEA)"),
        ("master_pro", "Génie climatique et maîtrise de l'énergie"),
        ("master_pro", "Systèmes intelligents communicants"),
        ("master_pro", "Ressources naturelles et valorisation"),
    ],
    "Mathématiques": [
        ("licence", "Mathématiques"),
        ("licence", "Mathématiques appliquées : Math-Info"),
        ("master_recherche", "Mathématiques"),
        ("master_pro", "Mathématiques et Data Science"),
    ],
    "Informatique": [
        ("licence", "Sciences de l'informatique : Génie logiciel et systèmes d'information"),
        ("licence", "Ingénierie des systèmes informatiques : Systèmes embarqués et IoT"),
        ("master_recherche", "Sciences informatiques"),
        ("master_pro", "Expert systèmes, réseaux et virtualisation"),
        ("master_pro", "Data Sciences"),
    ],
    "Chimie": [
        ("licence", "Chimie industrielle"),
        ("licence", "Chimie fine"),
        ("licence", "Chimie : parcours recherche"),
        ("master_recherche", "Chimie fondamentale : Inorganique"),
        ("master_recherche", "Chimie fondamentale : Organique"),
        ("master_pro", "Chimie industrielle et pétrochimie"),
        ("master_pro", "Analyses physico-chimiques et applications industrielles"),
    ],
    "Sciences biologiques": [
        ("licence", "Sciences de la vie et de la terre"),
        ("licence", "Sciences du vivant et de l'environnement : Biosurveillance des écosystèmes"),
        ("licence", "Sciences du vivant : Biologie moléculaire et cellulaire"),
        ("licence", "Biotechnologie : Contrôle qualité des aliments et hygiène"),
        ("master_recherche", "BMC-Biotech, parcours RFMA"),
        ("master_recherche", "BMC-Biotech, parcours PCMV"),
        ("master_recherche", "Biologie des organismes, des populations et de l'environnement"),
        ("master_pro", "Sécurité sanitaire des aliments (SSA)"),
        ("master_pro", "Surveillance et gestion intégrée de l'environnement"),
    ],
    "Sciences de la terre": [
        ("licence", "Sciences de la terre : Géo-ressources et environnement"),
        ("licence", "Sciences de la terre : Sciences et techniques de géologie"),
        ("master_recherche", "Géologie appliquée"),
        ("master_recherche", "Hydrogéosciences et environnement"),
        ("master_pro", "Géoressources et applications"),
    ],
    "Transversal": [
        ("master_pro", "Management et innovation technologique (co-construit)"),
    ],
}

FTS_EXPR = (
    "(setweight(to_tsvector('french', coalesce(title,'')), 'A') || "
    "setweight(to_tsvector('french', text), 'D'))"
)


def upgrade() -> None:
    # --- chat ---
    op.add_column("chat_sessions", sa.Column("title", sa.String(), nullable=True))
    op.add_column("chat_sessions", sa.Column("updated_at", sa.DateTime(), nullable=True))
    op.execute("UPDATE chat_sessions SET updated_at = created_at")
    op.execute("""
        UPDATE chat_sessions s SET title = LEFT(m.content, 80)
        FROM (SELECT DISTINCT ON (session_id) session_id, content FROM chat_messages
              WHERE role = 'user' ORDER BY session_id, created_at) m
        WHERE m.session_id = s.id AND s.title IS NULL
    """)
    op.add_column("chat_messages", sa.Column("grounded", sa.Boolean(), nullable=True))

    # --- classroom ---
    for name, type_ in (
        ("sync_status", sa.String()),
        ("sync_started_at", sa.Float()),
        ("sync_courses_synced", sa.Integer()),
        ("sync_materials_synced", sa.Integer()),
        ("sync_materials_failed", sa.Integer()),
        ("sync_error", sa.String()),
    ):
        op.add_column("google_classroom_accounts", sa.Column(name, type_, nullable=True))
    op.execute("UPDATE google_classroom_accounts SET sync_status = 'idle'")
    op.add_column("course_materials", sa.Column("due_at", sa.DateTime(), nullable=True))
    # Courses created by a Classroom sync are private to that student.
    op.execute("""
        UPDATE courses c SET source = 'google_classroom', external_id = sc.external_id
        FROM student_courses sc
        WHERE sc.course_id = c.id AND sc.source = 'google_classroom'
    """)

    # --- integrity (drop duplicates first so the constraints can be created) ---
    op.execute("""
        DELETE FROM student_courses a USING student_courses b
        WHERE a.student_id = b.student_id AND a.course_id = b.course_id
          AND a.enrolled_at > b.enrolled_at
    """)
    op.create_unique_constraint("uq_student_course", "student_courses", ["student_id", "course_id"])
    op.execute("""
        DELETE FROM feedback a USING feedback b
        WHERE a.chat_message_id = b.chat_message_id AND a.user_id = b.user_id AND a.id < b.id
    """)
    op.create_unique_constraint("uq_feedback_message_user", "feedback", ["chat_message_id", "user_id"])

    # --- programmes ---
    op.add_column("programs", sa.Column("level", sa.String(), nullable=True))
    op.add_column("students", sa.Column("program_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_students_program", "students", "programs", ["program_id"], ["id"])
    departments = sa.table("departments", sa.column("id", postgresql.UUID(as_uuid=True)), sa.column("name", sa.String()))
    programs = sa.table(
        "programs",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("name", sa.String()),
        sa.column("level", sa.String()),
        sa.column("department_id", postgresql.UUID(as_uuid=True)),
    )
    dept_rows, program_rows = [], []
    for dept_name, entries in DEPARTMENTS.items():
        dept_id = uuid.uuid4()
        dept_rows.append({"id": dept_id, "name": dept_name})
        program_rows += [
            {"id": uuid.uuid4(), "name": name, "level": level, "department_id": dept_id}
            for level, name in entries
        ]
    op.bulk_insert(departments, dept_rows)
    op.bulk_insert(programs, program_rows)

    # --- search indexes ---
    op.execute("CREATE INDEX IF NOT EXISTS ix_document_chunks_student_course ON document_chunks (student_id, course_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_document_chunks_material ON document_chunks (material_id)")
    op.execute(f"CREATE INDEX IF NOT EXISTS ix_document_chunks_fts ON document_chunks USING gin ({FTS_EXPR})")

    # --- unused tables ---
    op.drop_table("admission_scores")
    op.drop_table("recommendations")
    op.drop_table("audit_logs")


def downgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("students.id")),
        sa.Column("action", sa.String()),
        sa.Column("timestamp", sa.DateTime()),
    )
    op.create_table(
        "recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("students.id")),
        sa.Column("content", sa.Text()),
    )
    op.create_table(
        "admission_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("students.id")),
        sa.Column("score", sa.Float()),
    )
    op.execute("DROP INDEX IF EXISTS ix_document_chunks_fts")
    op.execute("DROP INDEX IF EXISTS ix_document_chunks_material")
    op.execute("DROP INDEX IF EXISTS ix_document_chunks_student_course")
    op.drop_constraint("fk_students_program", "students", type_="foreignkey")
    op.drop_column("students", "program_id")
    op.execute("DELETE FROM programs WHERE level IS NOT NULL")
    names = ", ".join("'" + n.replace("'", "''") + "'" for n in DEPARTMENTS)
    op.execute(f"DELETE FROM departments WHERE name IN ({names})")
    op.drop_column("programs", "level")
    op.drop_constraint("uq_feedback_message_user", "feedback", type_="unique")
    op.drop_constraint("uq_student_course", "student_courses", type_="unique")
    op.drop_column("course_materials", "due_at")
    for name in ("sync_error", "sync_materials_failed", "sync_materials_synced",
                 "sync_courses_synced", "sync_started_at", "sync_status"):
        op.drop_column("google_classroom_accounts", name)
    op.drop_column("chat_messages", "grounded")
    op.drop_column("chat_sessions", "updated_at")
    op.drop_column("chat_sessions", "title")
