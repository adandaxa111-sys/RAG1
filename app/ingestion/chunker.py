import re
from app.core.config import CHUNK_SIZE, CHUNK_OVERLAP


def split_into_chunks(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[str]:
    """Split text into overlapping chunks, breaking at sentence boundaries."""
    if not text.strip():
        return []

    sentences = re.split(r'(?<=[.!?])\s+', text)

    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        if len(current) + len(sentence) + 1 > chunk_size and current:
            chunks.append(current.strip())
            # Keep tail of previous chunk as overlap context
            overlap = current[-chunk_overlap:] if chunk_overlap > 0 else ""
            current = overlap + " " + sentence
        else:
            current = (current + " " + sentence).strip()

    if current.strip():
        chunks.append(current.strip())

    # If no sentence boundaries were found, force-split long text
    if not chunks and text.strip():
        chunks = [text.strip()]

    return chunks
