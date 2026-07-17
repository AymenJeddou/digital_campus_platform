"""Text extraction for uploaded course materials.

Supports the formats a student is realistically going to upload directly —
PDF, Word (.docx), and plain text/Markdown. Anything else, or a file that
turns out to hold no extractable text (e.g. a scanned PDF with no OCR
layer), is rejected with a clear, specific error rather than being silently
stored as an empty material — the same scope boundary already flagged in
CHANGES_classroom.md for Google Classroom's non-Doc attachments.
"""
import io

import docx  # python-docx
import pptx  # python-pptx
from pypdf import PdfReader
from pypdf.errors import PdfReadError

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".txt", ".md"}

# Sane ceiling so a single upload can't blow up chunking/embedding cost or
# time out the request. A "course material" is a handout or slide export,
# not a 300-page textbook — those belong in the knowledge base pipeline, not
# here.
MAX_PDF_PAGES = 300


class TextExtractionError(Exception):
    """Raised when a file can't be turned into usable text."""


class UnsupportedFileType(TextExtractionError):
    """Raised when the file extension isn't one we know how to read."""


def _extension(filename: str) -> str:
    filename = filename or ""
    return "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def extract_text(filename: str, content: bytes) -> str:
    """Extract plain text from an uploaded file's raw bytes.

    Raises `UnsupportedFileType` for an unrecognized extension, or
    `TextExtractionError` for a recognized-but-unreadable / empty file.
    """
    ext = _extension(filename)
    if ext not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise UnsupportedFileType(
            f"Unsupported file type '{ext or 'unknown'}'. Supported types: {supported}."
        )
    if ext == ".pdf":
        return _extract_pdf(content)
    if ext == ".docx":
        return _extract_docx(content)
    if ext == ".pptx":
        return _extract_pptx(content)
    return _extract_plain_text(content)


def _extract_pdf(content: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(content))
    except PdfReadError as exc:
        raise TextExtractionError(f"Could not read this PDF: {exc}") from exc

    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception as exc:  # noqa: BLE001 - pypdf raises varied errors here
            raise TextExtractionError(
                "This PDF is password-protected and can't be read."
            ) from exc

    if len(reader.pages) > MAX_PDF_PAGES:
        raise TextExtractionError(
            f"This PDF has {len(reader.pages)} pages, which exceeds the "
            f"{MAX_PDF_PAGES}-page limit for a single course material."
        )

    pages_text = []
    for page in reader.pages:
        try:
            pages_text.append(page.extract_text() or "")
        except Exception:  # noqa: BLE001 - skip an unreadable page, don't fail the upload
            continue

    text = "\n\n".join(t for t in pages_text if t.strip())
    if not text.strip():
        raise TextExtractionError(
            "No extractable text found in this PDF — it may be a scanned "
            "image without an OCR text layer, which isn't supported yet."
        )
    return text


def _extract_docx(content: bytes) -> str:
    try:
        document = docx.Document(io.BytesIO(content))
    except Exception as exc:  # noqa: BLE001 - python-docx raises varied errors here
        raise TextExtractionError(f"Could not read this Word document: {exc}") from exc

    parts = [p.text for p in document.paragraphs if p.text.strip()]
    for table in document.tables:
        for row in table.rows:
            row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
            if row_text:
                parts.append(row_text)

    text = "\n".join(parts)
    if not text.strip():
        raise TextExtractionError("No extractable text found in this document.")
    return text


def _extract_plain_text(content: bytes) -> str:
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            text = content.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise TextExtractionError("Could not decode this file as text.")

    if not text.strip():
        raise TextExtractionError("The uploaded file is empty.")
    return text


def _extract_pptx(content: bytes) -> str:
    try:
        prs = pptx.Presentation(io.BytesIO(content))
    except Exception as exc:
        raise TextExtractionError(f"Could not read this PowerPoint presentation: {exc}") from exc

    parts = []
    for slide in prs.slides:
        slide_parts = []
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                slide_parts.append(shape.text.strip())
            if shape.has_table:
                for row in shape.table.rows:
                    row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                    if row_text:
                        slide_parts.append(row_text)
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
            notes = slide.notes_slide.notes_text_frame.text.strip()
            if notes:
                slide_parts.append(f"[Note de diapositive] {notes}")
        
        slide_text = "\n".join(slide_parts)
        if slide_text:
            parts.append(slide_text)

    text = "\n\n".join(parts)
    if not text.strip():
        raise TextExtractionError("No extractable text found in this presentation.")
    return text
