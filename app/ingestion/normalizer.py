import re
import unicodedata


def normalize_text(text: str) -> str:
    """Clean up raw text: fix encoding artifacts, collapse whitespace, strip control chars."""
    text = unicodedata.normalize("NFKC", text)

    # Remove control characters except newlines and tabs
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)

    # Collapse 3+ newlines into 2
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Collapse runs of spaces/tabs (not newlines) into single space
    text = re.sub(r'[^\S\n]+', ' ', text)

    # Strip leading/trailing whitespace per line
    text = '\n'.join(line.strip() for line in text.splitlines())

    return text.strip()
