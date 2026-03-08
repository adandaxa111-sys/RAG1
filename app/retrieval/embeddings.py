import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.config import EMBEDDING_MODEL
from app.core.logging import log


class Embedder:
    """Wraps sentence-transformers for encoding text to vectors."""

    def __init__(self, model_name: str = EMBEDDING_MODEL):
        log.info(f"Loading embedding model: {model_name} ...")
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        log.info(f"Embedding model ready — dimension={self.dimension}")

    def encode(self, texts: list[str]) -> np.ndarray:
        vectors = self.model.encode(
            texts,
            prompt_name="document",
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        return np.array(vectors, dtype=np.float32)

    def encode_query(self, query: str) -> np.ndarray:
        vectors = self.model.encode(
            [query],
            prompt_name="query",
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        return np.array(vectors, dtype=np.float32)
