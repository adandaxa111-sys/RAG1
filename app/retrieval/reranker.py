import numpy as np
from sentence_transformers import CrossEncoder

from app.core.config import RERANKER_MODEL
from app.core.logging import log
from app.retrieval.store_schema import ChunkMeta


class Reranker:
    """Cross-encoder reranker — scores (query, chunk) pairs and reorders by relevance."""

    def __init__(self, model_name: str = RERANKER_MODEL):
        log.info(f"Loading reranker model: {model_name} ...")
        self.model = CrossEncoder(model_name)
        log.info("Reranker model ready")

    def rerank(
        self, query: str, chunks: list[ChunkMeta], top_n: int
    ) -> list[tuple[ChunkMeta, float]]:
        """Score every (query, chunk) pair and return top_n as (chunk, score) tuples."""
        if not chunks:
            return []

        pairs = [(query, chunk.text) for chunk in chunks]
        scores: np.ndarray = self.model.predict(pairs)

        scored = sorted(zip(scores, chunks), key=lambda x: x[0], reverse=True)
        top = [(chunk, float(score)) for score, chunk in scored[:top_n]]

        log.info(
            f"Reranked {len(chunks)} candidates → kept top {len(top)} "
            f"(scores: {scored[0][0]:.3f} … {scored[-1][0]:.3f})"
        )
        return top
