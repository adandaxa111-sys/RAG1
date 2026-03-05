import os
from pathlib import Path

# ── Paths ──
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
INDEX_DIR = DATA_DIR / "index"
STATIC_DIR = PROJECT_ROOT / "static"

CHUNKS_FILE = PROCESSED_DIR / "chunks.jsonl"
DOCS_FILE = PROCESSED_DIR / "docs.jsonl"
FAISS_INDEX_FILE = INDEX_DIR / "faiss.index"

for d in (RAW_DIR, PROCESSED_DIR, INDEX_DIR):
    d.mkdir(parents=True, exist_ok=True)

# ── Embedding ──
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")

# ── Chunking ──
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))

# ── Retrieval ──
TOP_K = int(os.getenv("TOP_K", "5"))

# ── LLM (LM Studio or any OpenAI-compatible server) ──
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://127.0.0.1:1234/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "lm-studio")
LLM_MODEL = os.getenv("LLM_MODEL", "gemma-3-4b-it")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "1024"))

# ── Server ──
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))
