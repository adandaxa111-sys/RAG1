from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from pydantic import BaseModel

router = APIRouter()

# Will be set by main.py after pipeline init
pipeline = None


def set_pipeline(p):
    global pipeline
    pipeline = p


# ── Request / Response Models ──

class TextIngestRequest(BaseModel):
    text: str
    document_name: Optional[str] = "Untitled Document"


class QueryRequest(BaseModel):
    question: str


class SourceInfo(BaseModel):
    document_name: str
    chunk_id: int
    chunk_text: Optional[str] = None
    rerank_score: Optional[float] = None


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceInfo]


class DocumentInfo(BaseModel):
    name: str
    chunks: int
    doc_id: Optional[str] = None


class DocumentsResponse(BaseModel):
    documents: list[DocumentInfo]


class IngestResponse(BaseModel):
    message: str
    document_name: str
    chunks_added: int


class HealthResponse(BaseModel):
    status: str
    documents: int
    chunks: int


class DeleteResponse(BaseModel):
    message: str
    doc_id: str


class ChunkInfo(BaseModel):
    chunk_id: str
    doc_id: str
    document_name: str
    chunk_index: int
    text: str
    char_offset: int
    char_length: int


class ChunksResponse(BaseModel):
    chunks: list[ChunkInfo]
    total: int


class StatsResponse(BaseModel):
    total_vectors: int
    dimension: int
    index_type: str
    total_documents: int
    total_chunks: int
    embedding_model: str
    reranker_enabled: bool


class RawSearchRequest(BaseModel):
    question: str
    top_k: Optional[int] = None


class RawSearchResult(BaseModel):
    document_name: str
    chunk_id: int
    chunk_text: str
    score: float
    score_type: str


class RawSearchResponse(BaseModel):
    question: str
    results: list[RawSearchResult]


# ── Endpoints ──

@router.post("/ingest", response_model=IngestResponse)
async def ingest_file(file: UploadFile = File(...)):
    """Ingest a document file into the knowledge base."""
    content = await file.read()
    filename = file.filename or "upload.txt"

    result = pipeline.ingest_file(filename, content)

    return IngestResponse(
        message="Document ingested successfully",
        document_name=result["document_name"],
        chunks_added=result["chunks_added"],
    )


@router.post("/ingest_text", response_model=IngestResponse)
async def ingest_text(req: TextIngestRequest):
    """Ingest raw text as a document."""
    result = pipeline.ingest_text(req.document_name, req.text)

    return IngestResponse(
        message="Document ingested successfully",
        document_name=result["document_name"],
        chunks_added=result["chunks_added"],
    )


@router.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    """Ask a question against the knowledge base."""
    if not pipeline.has_documents():
        raise HTTPException(
            status_code=400,
            detail="No documents in the knowledge base. Please ingest documents first.",
        )

    result = pipeline.query(req.question)

    return QueryResponse(
        answer=result["answer"],
        sources=[SourceInfo(**s) for s in result["sources"]],
    )


@router.get("/documents", response_model=DocumentsResponse)
async def list_documents():
    """List all ingested documents."""
    docs = pipeline.list_documents()
    return DocumentsResponse(documents=[DocumentInfo(**d) for d in docs])


@router.delete("/documents/{doc_id}", response_model=DeleteResponse)
async def delete_document(doc_id: str):
    """Remove a document and all its chunks from the knowledge base."""
    deleted = pipeline.delete_document(doc_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found.")
    return DeleteResponse(message="Document deleted successfully", doc_id=doc_id)


@router.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        documents=len(pipeline.list_documents()),
        chunks=pipeline.store.total_chunks,
    )


@router.get("/chunks", response_model=ChunksResponse)
async def list_chunks(doc_id: Optional[str] = Query(default=None)):
    """List all stored chunks, optionally filtered by document ID."""
    chunks = pipeline.list_chunks(doc_id)
    return ChunksResponse(chunks=chunks, total=len(chunks))


@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Return vector store and model statistics."""
    return StatsResponse(**pipeline.get_stats())


@router.post("/search_raw", response_model=RawSearchResponse)
async def search_raw(req: RawSearchRequest):
    """Semantic search: return top-k chunks with scores, no LLM generation."""
    if not pipeline.has_documents():
        raise HTTPException(
            status_code=400,
            detail="No documents in the knowledge base. Please ingest documents first.",
        )
    from app.core.config import TOP_K
    results = pipeline.search_raw(req.question, top_k=req.top_k or TOP_K)
    return RawSearchResponse(question=req.question, results=results)
