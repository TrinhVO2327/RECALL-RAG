"""Document ingestion: extracts text from files and split into chunks."""

import io
import pdfplumber


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Pull all text out of a PDF given its raw bytes."""
    text_parts: list[str] = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)

def chunk_text(text: str, chunk_size: int = 800, overlap: int =150) -> list[str]:
    """Split text into overlapping chunks of roughly chunk_size characrers."""
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be greater than overlap")
    
    text=text.strip()
    if not text:
        return []
    
    chunks: list[str] = []
    start = 0
    step = chunk_size - overlap
    while start < len(text):
        end = start + chunk_size
        chunk = text[start : end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start += step
    return chunks