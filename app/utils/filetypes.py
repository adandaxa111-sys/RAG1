from pathlib import Path

SUPPORTED_EXTENSIONS = {
    ".txt", ".md", ".csv", ".json", ".pdf", ".log",
    ".html", ".htm", ".xml",
    ".doc", ".docx",
    ".pptx",
    ".xlsx", ".xls",
    ".rtf",
}


def is_supported(filename: str) -> bool:
    return Path(filename).suffix.lower() in SUPPORTED_EXTENSIONS


def get_extension(filename: str) -> str:
    return Path(filename).suffix.lower()
