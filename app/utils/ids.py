import uuid
import hashlib


def generate_doc_id(name: str) -> str:
    """Deterministic document ID based on name + random salt to allow re-ingestion."""
    salt = uuid.uuid4().hex[:8]
    return hashlib.sha256(f"{name}:{salt}".encode()).hexdigest()[:16]


def generate_chunk_id(doc_id: str, chunk_index: int) -> str:
    return f"{doc_id}_{chunk_index:04d}"
