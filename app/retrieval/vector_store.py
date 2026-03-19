import json

import faiss
import numpy as np

from app.core.config import FAISS_INDEX_FILE, VECTORS_FILE, CHUNKS_FILE, DOCS_FILE, TOP_K
from app.core.logging import log
from app.retrieval.store_schema import ChunkMeta, DocMeta


class VectorStore:
    """FAISS-backed vector store with JSON-lines metadata persistence."""

    def __init__(self, dimension: int):
        self.dimension = dimension
        self.chunks: list[ChunkMeta] = []
        self.vectors: list[np.ndarray] = []   # mirrors self.chunks, one vector per chunk
        self.docs: dict[str, DocMeta] = {}
        self.index = faiss.IndexFlatIP(dimension)

        self._load_from_disk()

    # ── Add ──

    def add(self, embeddings: np.ndarray, chunk_metas: list[ChunkMeta], doc_meta: DocMeta):
        self.index.add(embeddings)
        self.chunks.extend(chunk_metas)
        self.vectors.extend(embeddings)
        self.docs[doc_meta.doc_id] = doc_meta

        self._save_to_disk()
        log.info(f"Stored {len(chunk_metas)} chunks for '{doc_meta.name}' (total: {self.index.ntotal})")

    # ── Delete ──

    def delete_document(self, doc_id: str) -> bool:
        """Remove a document and rebuild the FAISS index from remaining vectors."""
        if doc_id not in self.docs:
            return False

        doc_name = self.docs[doc_id].name
        keep = [(c, v) for c, v in zip(self.chunks, self.vectors) if c.doc_id != doc_id]

        if keep:
            self.chunks, vecs = zip(*keep)
            self.chunks = list(self.chunks)
            self.vectors = list(vecs)
        else:
            self.chunks = []
            self.vectors = []

        # Rebuild FAISS index from surviving vectors
        self.index = faiss.IndexFlatIP(self.dimension)
        if self.vectors:
            self.index.add(np.array(self.vectors, dtype=np.float32))

        del self.docs[doc_id]
        self._save_to_disk()
        log.info(f"Deleted '{doc_name}' — {self.index.ntotal} vectors remaining")
        return True

    # ── Search ──

    def search(self, query_vector: np.ndarray, top_k: int = TOP_K) -> list[ChunkMeta]:
        if self.index.ntotal == 0:
            return []

        k = min(top_k, self.index.ntotal)
        scores, indices = self.index.search(query_vector, k)

        return [self.chunks[idx] for idx in indices[0] if 0 <= idx < len(self.chunks)]

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

    def list_chunks(self, doc_id: str | None = None) -> list[dict]:
        """Return all chunk metadata, optionally filtered by document."""
        return [
            c.to_dict()
            for c in self.chunks
            if doc_id is None or c.doc_id == doc_id
        ]

    def get_stats(self) -> dict:
        return {
            "total_vectors": self.index.ntotal,
            "dimension": self.dimension,
            "index_type": "IndexFlatIP",
            "total_documents": len(self.docs),
            "total_chunks": len(self.chunks),
        }

    def search_with_scores(self, query_vector: np.ndarray, top_k: int = TOP_K) -> list[tuple]:
        """Return (ChunkMeta, cosine_score) pairs for the top-k results."""
        if self.index.ntotal == 0:
            return []
        k = min(top_k, self.index.ntotal)
        scores, indices = self.index.search(query_vector, k)
        return [
            (self.chunks[idx], float(scores[0][i]))
            for i, idx in enumerate(indices[0])
            if 0 <= idx < len(self.chunks)
        ]

    # ── Persistence ──

    def _save_to_disk(self):
        try:
            faiss.write_index(self.index, str(FAISS_INDEX_FILE))

            if self.vectors:
                np.save(str(VECTORS_FILE), np.array(self.vectors, dtype=np.float32))
            elif VECTORS_FILE.exists():
                VECTORS_FILE.unlink()

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

            if VECTORS_FILE.exists():
                loaded = np.load(str(VECTORS_FILE))
                self.vectors = list(loaded)

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
