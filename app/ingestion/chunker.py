import re
from app.core.config import CHUNK_SIZE, CHUNK_OVERLAP

# Splits on:
#   • one or more blank lines  (\n\n+)  — paragraph / JSON-record boundaries
#   • sentence-ending punctuation followed by whitespace
_UNIT_SPLIT = re.compile(r'\n\n+|(?<=[.!?])\s+')


def split_into_chunks(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[str]:
    """Split text into overlapping chunks.

    Units are paragraphs (blank-line separated) or sentences (punctuation
    separated), whichever boundary comes first.  This means JSON records,
    markdown sections, and PDF paragraphs all get proper chunk boundaries
    even when the text contains no sentence-ending punctuation.
    """
    if not text.strip():
        return []

    units = [u for u in _UNIT_SPLIT.split(text) if u.strip()]

    if not units:
        return [text.strip()]

    chunks: list[str] = []
    current = ""

    for unit in units:
        candidate = (current + "\n\n" + unit).strip() if current else unit.strip()
        if len(candidate) > chunk_size and current:
            chunks.append(current.strip())
            overlap = current[-chunk_overlap:] if chunk_overlap > 0 else ""
            current = (overlap + "\n\n" + unit).strip() if overlap else unit.strip()
        else:
            current = candidate

    if current.strip():
        chunks.append(current.strip())

    # Last-resort: single block that exceeds chunk_size — return as-is
    if not chunks and text.strip():
        chunks = [text.strip()]

    return chunks
