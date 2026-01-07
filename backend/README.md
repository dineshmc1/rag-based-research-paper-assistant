# Research RAG Assistant - Backend

A production-grade RAG (Retrieval-Augmented Generation) system for research papers with Deep RAG capabilities.

## Features

- **PDF Ingestion**: Parse research PDFs with page-level fidelity
- **Semantic Chunking**: Sentence-aware chunking with sliding window
- **Deep RAG Pipeline**:
  - Query expansion (LLM-based)
  - Parallel vector search
  - Cross-encoder reranking
  - Citation-grounded answer synthesis
- **Knowledge Graph**: Automatic concept extraction and relationship mapping
- **Vector Store**: ChromaDB for efficient similarity search

## Tech Stack

- FastAPI
- PyMuPDF (PDF parsing)
- ChromaDB (vector database)
- Sentence-Transformers (embeddings)
- Cross-Encoder (reranking)
- OpenAI GPT-4o-mini (answer synthesis)

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` file (see `.env.example`):
```bash
cp .env.example .env
# Edit .env with your OpenAI API key
```

3. Run the server:
```bash
uvicorn app.main:app --reload --port 8000
```

## API Endpoints

### Ingest
- `POST /api/ingest/upload` - Upload and process PDF
- `DELETE /api/ingest/paper/{paper_id}` - Delete paper

### Chat
- `POST /api/chat/query` - Query papers with Deep RAG

### Papers
- `GET /api/papers/list` - List all papers
- `GET /api/papers/{paper_id}/download` - Download PDF
- `GET /api/papers/{paper_id}/chunks` - Get paper chunks

### Graph
- `GET /api/graph/{paper_id}` - Get knowledge graph

## Architecture

```
┌─────────────┐
│   FastAPI   │
└──────┬──────┘
       │
       ├─── PDF Parser (PyMuPDF)
       │
       ├─── Semantic Chunker
       │
       ├─── Embeddings (all-MiniLM-L6-v2)
       │
       ├─── ChromaDB (Vector Store)
       │
       ├─── Query Expander (GPT-4o-mini)
       │
       ├─── Reranker (Cross-Encoder)
       │
       └─── Answer Synthesizer (GPT-4o-mini)
```

## RAG Pipeline Flow

1. **Upload**: PDF → Pages → Semantic Chunks → Embeddings → ChromaDB
2. **Query**: 
   - User Query → Query Expansion (3 variants)
   - Parallel Vector Search (all variants)
   - Deduplicate Results
   - Cross-Encoder Reranking (top-K)
   - Answer Synthesis with Citations
   - Concept Extraction

## Configuration

All settings in `app/core/config.py` can be overridden via environment variables.

Key parameters:
- `CHUNK_SIZE`: Token count per chunk (default: 400)
- `CHUNK_OVERLAP`: Overlap between chunks (default: 50)
- `TOP_K_RETRIEVAL`: Initial retrieval count (default: 20)
- `TOP_K_RERANKED`: Final reranked count (default: 5)
- `NUM_QUERY_VARIANTS`: Query expansion variants (default: 3)
