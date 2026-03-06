from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException
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
