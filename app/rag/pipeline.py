from app.retrieval.embeddings import Embedder
from app.retrieval.reranker import Reranker
from app.retrieval.vector_store import VectorStore
from app.retrieval.store_schema import ChunkMeta, DocMeta
from app.ingestion.loader import load_text_from_bytes
from app.ingestion.normalizer import normalize_text
from app.ingestion.chunker import split_into_chunks
from app.llm.lmstudio_client import LMStudioClient
from app.llm.types import LLMRequest
from app.rag.prompt import SYSTEM_PROMPT, build_context, build_user_prompt
from app.utils.ids import generate_doc_id, generate_chunk_id
from app.utils.paths import safe_save_path
from app.core.config import TOP_K, RERANKER_ENABLED, RERANKER_CANDIDATES
from app.core.logging import log


class RAGPipeline:
    """End-to-end RAG: ingest documents, retrieve chunks, generate answers."""

    def __init__(self):
        self.embedder = Embedder()
        self.store = VectorStore(dimension=self.embedder.dimension)
        self.llm = LMStudioClient()
        self.reranker = Reranker() if RERANKER_ENABLED else None
        if self.reranker:
            log.info("Reranker enabled")
        else:
            log.info("Reranker disabled")

    # ── Ingest ──

    def ingest_file(self, filename: str, content: bytes) -> dict:
        """Ingest a file: load → normalize → chunk → embed → store."""
        save_path = safe_save_path(filename)
        save_path.write_bytes(content)

        raw_text = load_text_from_bytes(content, filename)
        return self._ingest_text(filename, raw_text)

    def ingest_text(self, document_name: str, text: str) -> dict:
        """Ingest raw text directly."""
        return self._ingest_text(document_name, text)

    def _ingest_text(self, document_name: str, raw_text: str) -> dict:
        clean_text = normalize_text(raw_text)
        chunks_text = split_into_chunks(clean_text)

        if not chunks_text:
            return {"document_name": document_name, "chunks_added": 0}

        doc_id = generate_doc_id(document_name)

        chunk_metas = []
        offset = 0
        for i, text in enumerate(chunks_text):
            chunk_metas.append(ChunkMeta(
                chunk_id=generate_chunk_id(doc_id, i),
                doc_id=doc_id,
                document_name=document_name,
                chunk_index=i,
                text=text,
                char_offset=offset,
                char_length=len(text),
            ))
            offset += len(text)

        embeddings = self.embedder.encode([c.text for c in chunk_metas])

        doc_meta = DocMeta(
            doc_id=doc_id,
            name=document_name,
            chunk_count=len(chunk_metas),
        )

        self.store.add(embeddings, chunk_metas, doc_meta)

        log.info(f"Ingested '{document_name}': {len(chunk_metas)} chunks")
        return {
            "document_name": document_name,
            "doc_id": doc_id,
            "chunks_added": len(chunk_metas),
        }

    # ── Query ──

    def query(self, question: str, top_k: int = TOP_K) -> dict:
        """Retrieve relevant chunks and generate an LLM answer."""
        query_vec = self.embedder.encode_query(question)

        if self.reranker:
            # Fetch more candidates then rerank down to top_k
            candidates = self.store.search(query_vec, top_k=RERANKER_CANDIDATES)
            ranked = self.reranker.rerank(question, candidates, top_n=top_k)
            retrieved = [chunk for chunk, _ in ranked]
            scores = [score for _, score in ranked]
        else:
            retrieved = self.store.search(query_vec, top_k=top_k)
            scores = [None] * len(retrieved)

        context = build_context(retrieved)

        try:
            llm_response = self.llm.generate(LLMRequest(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=build_user_prompt(question, context),
            ))
            answer = llm_response.content
        except Exception as e:
            log.warning(f"LLM unavailable, returning raw context: {e}")
            answer = (
                "LLM server is not reachable. Showing retrieved context:\n\n"
                + context
            )

        sources = [
            {
                "document_name": c.document_name,
                "chunk_id": c.chunk_index,
                "chunk_text": c.text,
                "rerank_score": score,
            }
            for c, score in zip(retrieved, scores)
        ]

        return {"answer": answer, "sources": sources}

    # ── Delete ──

    def delete_document(self, doc_id: str) -> bool:
        return self.store.delete_document(doc_id)

    # ── State ──

    def has_documents(self) -> bool:
        return self.store.has_documents()

    def list_documents(self) -> list[dict]:
        return self.store.list_documents()

    def list_chunks(self, doc_id: str | None = None) -> list[dict]:
        return self.store.list_chunks(doc_id)

    def get_stats(self) -> dict:
        stats = self.store.get_stats()
        stats["embedding_model"] = self.embedder.model_name
        stats["reranker_enabled"] = RERANKER_ENABLED
        return stats

    def search_raw(self, question: str, top_k: int = TOP_K) -> list[dict]:
        """Retrieve top-k chunks with relevance scores — no LLM involved."""
        query_vec = self.embedder.encode_query(question)

        if self.reranker:
            candidates = self.store.search(query_vec, top_k=RERANKER_CANDIDATES)
            ranked = self.reranker.rerank(question, candidates, top_n=top_k)
            return [
                {
                    "document_name": chunk.document_name,
                    "chunk_id": chunk.chunk_index,
                    "chunk_text": chunk.text,
                    "score": float(score),
                    "score_type": "rerank",
                }
                for chunk, score in ranked
            ]

        results = self.store.search_with_scores(query_vec, top_k=top_k)
        return [
            {
                "document_name": chunk.document_name,
                "chunk_id": chunk.chunk_index,
                "chunk_text": chunk.text,
                "score": score,
                "score_type": "cosine",
            }
            for chunk, score in results
        ]
