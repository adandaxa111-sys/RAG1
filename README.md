# RAG Document Q&A

A Retrieval-Augmented Generation service that lets users ask questions about uploaded documents.
Supports Hebrew and English with automatic RTL/LTR text direction detection.

## Setup

```bash
pip install -r requirements.txt
```

### HuggingFace Login (required for gated models)

The default embedding model (`google/embeddinggemma-300m`) is gated. Before first run:

1. Accept the terms at https://huggingface.co/google/embeddinggemma-300m
2. Log in with your HuggingFace token:

```bash
python3 -c "from huggingface_hub import login; login('YOUR_TOKEN')"
```

Get a token (Read access) at https://huggingface.co/settings/tokens

## Running

```bash
python3 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000 in your browser.

On first startup the embedding and reranker models will be downloaded (~1 GB total).

## Configuration

All settings are in `app/core/config.py` and can be overridden via environment variables:

| Variable | Default | Description |
|---|---|---|
| `EMBEDDING_MODEL` | `google/embeddinggemma-300m` | Sentence-transformers embedding model |
| `CHUNK_SIZE` | `500` | Max characters per chunk |
| `CHUNK_OVERLAP` | `50` | Character overlap between chunks |
| `TOP_K` | `5` | Final number of chunks sent to the LLM |
| `RERANKER_ENABLED` | `true` | Enable/disable the cross-encoder reranker |
| `RERANKER_MODEL` | `BAAI/bge-reranker-v2-m3` | Cross-encoder reranker model |
| `RERANKER_CANDIDATES` | `15` | Chunks fetched from FAISS before reranking |
| `LLM_BASE_URL` | `http://127.0.0.1:1234/v1` | LM Studio / OpenAI-compatible endpoint |
| `LLM_API_KEY` | `lm-studio` | API key for the LLM server |
| `LLM_MODEL` | `gemma-3-12b-it` | Model name loaded in LM Studio |
| `LLM_TEMPERATURE` | `0.2` | Sampling temperature |
| `LLM_MAX_TOKENS` | `1024` | Max tokens in LLM response |

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/ingest` | Upload a file to the knowledge base |
| `POST` | `/ingest_text` | Add raw text as a document (JSON body) |
| `POST` | `/query` | Ask a question, get answer + sources with reranker scores |
| `GET` | `/documents` | List all ingested documents |
| `DELETE` | `/documents/{doc_id}` | Remove a document from the knowledge base |
| `GET` | `/health` | Health check |

## Architecture

```
app/
  api/routes.py          # REST endpoints
  core/config.py         # All configuration
  ingestion/             # Load, normalize, chunk documents
  retrieval/
    embeddings.py        # google/embeddinggemma-300m (768-dim, multilingual)
    reranker.py          # BAAI/bge-reranker-v2-m3 cross-encoder reranker
    vector_store.py      # FAISS IndexFlatIP + JSON-lines persistence
    store_schema.py      # ChunkMeta / DocMeta dataclasses
  rag/                   # Prompt building + end-to-end pipeline
  llm/                   # LM Studio client (OpenAI-compatible)
  utils/                 # ID generation, file type detection, paths
data/
  raw/                   # Uploaded source files
  processed/             # chunks.jsonl + docs.jsonl
  index/                 # faiss.index + vectors.npy
static/                  # Frontend (HTML / CSS / JS)
```

## Retrieval Pipeline

```
Query
  │
  ▼
FAISS vector search (RERANKER_CANDIDATES=15 chunks)
  │
  ▼
Cross-encoder reranker scores every (query, chunk) pair
  │
  ▼
Top TOP_K=5 chunks kept, scores shown in UI
  │
  ▼
LLM generates answer grounded in retrieved context
```

## Supported File Types

`.txt` `.pdf` `.docx` `.pptx` `.xlsx` `.xls` `.csv` `.md` `.rtf` `.html` `.htm` `.xml` `.json` `.log`
