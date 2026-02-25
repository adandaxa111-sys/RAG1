# RAG Document Q&A

A Retrieval-Augmented Generation service that lets users ask questions about uploaded documents.

## Setup

```bash
pip install -r requirements.txt
```

## Running

```bash
# Start the server
python -m uvicorn app.main:app --reload --port 8000
```

Or use the convenience script:
```powershell
.\scripts\dev_run.ps1
```

Open http://localhost:8000 in your browser.

## Configuration

All settings are in `app/core/config.py` and can be overridden via environment variables:

| Variable | Default | Description |
|---|---|---|
| `EMBEDDING_MODEL` | `BAAI/bge-m3` | Sentence-transformers embedding model |
| `CHUNK_SIZE` | `500` | Max characters per chunk |
| `CHUNK_OVERLAP` | `50` | Character overlap between chunks |
| `TOP_K` | `5` | Number of chunks to retrieve |
| `LLM_BASE_URL` | `http://localhost:1234/v1` | LM Studio / OpenAI-compatible endpoint |
| `LLM_API_KEY` | `lm-studio` | API key for the LLM server |
| `LLM_MODEL` | `local-model` | Model name to request |

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/ingest` | Upload a file to the knowledge base |
| `POST` | `/ingest_text` | Add raw text as a document (JSON body) |
| `POST` | `/query` | Ask a question, get answer + sources |
| `GET` | `/documents` | List all ingested documents |
| `GET` | `/health` | Health check |

## Architecture

```
app/
  api/routes.py          # REST endpoints
  core/config.py         # All configuration
  ingestion/             # Load, normalize, chunk documents
  retrieval/             # Embeddings (BAAI/bge-m3) + FAISS vector store
  rag/                   # Prompt building + end-to-end pipeline
  llm/                   # LM Studio client (OpenAI-compatible)
  utils/                 # ID generation, file type detection, paths
data/
  raw/                   # Uploaded source files
  processed/             # chunks.jsonl + docs.jsonl
  index/                 # Persisted FAISS index
```
