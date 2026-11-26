"""Extract text from uploaded CVs entirely in memory (nothing is written to disk)."""
import io

MAX_BYTES = 5 * 1024 * 1024


class CVExtractionError(Exception):
    """Raised with a user-friendly message when a CV cannot be read."""


def _read_pdf(data: bytes) -> str:
    import fitz  # PyMuPDF
    try:
        with fitz.open(stream=data, filetype="pdf") as doc:
            if doc.needs_pass:
                raise CVExtractionError("This PDF is password-protected. Please upload an unlocked copy.")
            return "\n".join(page.get_text() for page in doc)
    except CVExtractionError:
        raise
    except Exception as exc:
        raise CVExtractionError(f"Could not read the PDF ({exc}). The file may be corrupted.") from exc


def _read_docx(data: bytes) -> str:
    import docx  # python-docx
    try:
        document = docx.Document(io.BytesIO(data))
    except Exception as exc:
        raise CVExtractionError(f"Could not read the DOCX file ({exc}). Is it a valid .docx?") from exc
    parts = [p.text for p in document.paragraphs]
    for table in document.tables:
        for row in table.rows:
            parts.extend(cell.text for cell in row.cells)
    return "\n".join(parts)


def extract_text(filename: str, data: bytes) -> str:
    if not data:
        raise CVExtractionError("The uploaded file is empty.")
    if len(data) > MAX_BYTES:
        raise CVExtractionError("File is larger than 5 MB. Please upload a smaller CV.")
    name = filename.lower()
    if name.endswith(".pdf"):
        text = _read_pdf(data)
    elif name.endswith(".docx"):
        text = _read_docx(data)
    else:
        raise CVExtractionError("Unsupported file type. Please upload a PDF or DOCX file.")
    if len(text.strip()) < 30:
        raise CVExtractionError("Almost no text was found. Scanned/image-only CVs are not supported "
                                "(no OCR). Try a text-based PDF or DOCX.")
    return text
