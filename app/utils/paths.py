from pathlib import Path
from app.core.config import RAW_DIR


def safe_save_path(filename: str) -> Path:
    """Return a safe path inside RAW_DIR, stripping directory traversal attempts."""
    clean_name = Path(filename).name
    return RAW_DIR / clean_name
