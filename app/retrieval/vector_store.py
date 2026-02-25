import json
from pathlib import Path

import faiss
import numpy as np

from app.core.config import FAISS_INDEX_FILE, CHUNKS_FILE, DOCS_FILE, TOP_K
from app.core.logging import log
from app.retrieval.store_schema import ChunkMeta, DocMeta


class VectorStore:
    """FAISS-backed vector store with JSON-lines metadata persistence."""

    def __init__(self, dimension: int):
        self.dimension = dimension
        self.chunks: list[ChunkMeta] = []
        self.docs: dict[str, DocMeta] = {}
        self.index = faiss.IndexFlatIP(dimension)  # Inner product (cosine with normalized vecs)

        self._load_from_disk()

    # ── Add ──

    def add(self, embeddings: np.ndarray, chunk_metas: list[ChunkMeta], doc_meta: DocMeta):
        self.index.add(embeddings)
        self.chunks.extend(chunk_metas)
        self.docs[doc_meta.doc_id] = doc_meta

        self._save_to_disk()
        log.info(f"Stored {len(chunk_metas)} chunks for '{doc_meta.name}' (total vectors: {self.index.ntotal})")

    # ── Search ──

    def search(self, query_vector: np.ndarray, top_k: int = TOP_K) -> list[ChunkMeta]:
        if self.index.ntotal == 0:
            return []

        k = min(top_k, self.index.ntotal)
        scores, indices = self.index.search(query_vector, k)

        results = []
        for idx in indices[0]:
            if 0 <= idx < len(self.chunks):
                results.append(self.chunks[idx])
        return results

    # ── State ──

    @property
    def total_chunks(self) -> int:
        return self.index.ntotal

    def has_documents(self) -> bool:
        return self.index.ntotal > 0

    def list_documents(self) -> list[dict]:
        return [
            {"name": d.name, "chunks": d.chunk_count, "doc_id": d.doc_id}
            for d in self.docs.values()
        ]

    # ── Persistence ──

    def _save_to_disk(self):
        try:
            faiss.write_index(self.index, str(FAISS_INDEX_FILE))

            with open(CHUNKS_FILE, "w", encoding="utf-8") as f:
                for c in self.chunks:
                    f.write(json.dumps(c.to_dict(), ensure_ascii=False) + "\n")

            with open(DOCS_FILE, "w", encoding="utf-8") as f:
                for d in self.docs.values():
                    f.write(json.dumps(d.to_dict(), ensure_ascii=False) + "\n")

        except Exception as e:
            log.error(f"Failed to save index to disk: {e}")

    def _load_from_disk(self):
        if not FAISS_INDEX_FILE.exists():
            return

        try:
            self.index = faiss.read_index(str(FAISS_INDEX_FILE))
            log.info(f"Loaded FAISS index: {self.index.ntotal} vectors")

            if CHUNKS_FILE.exists():
                with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
                    self.chunks = [ChunkMeta.from_dict(json.loads(line)) for line in f if line.strip()]

            if DOCS_FILE.exists():
                with open(DOCS_FILE, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            d = DocMeta.from_dict(json.loads(line))
                            self.docs[d.doc_id] = d

            log.info(f"Loaded {len(self.chunks)} chunks, {len(self.docs)} documents from disk")
        except Exception as e:
            log.error(f"Failed to load index from disk: {e}")
