from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class ChunkMeta:
    chunk_id: str
    doc_id: str
    document_name: str
    chunk_index: int
    text: str
    char_offset: int = 0
    char_length: int = 0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "ChunkMeta":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class DocMeta:
    doc_id: str
    name: str
    chunk_count: int
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "DocMeta":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})
