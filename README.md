# Education Chatbot

Education Chatbot is a full-stack Retrieval-Augmented Generation (RAG) assistant designed for managing study materials and delivering grounded answers. The backend is built with FastAPI and uses hybrid FAISS + BM25 retrieval, optional reranking, and Ollama-powered generation. The frontend is a Vite/React dashboard for uploading documents, organizing subjects, and chatting with the assistant.

## Table of Contents
- [Repository Structure](#repository-structure)
- [Backend](#backend)
  - [Requirements](#requirements)
  - [Setup](#setup)
  - [Environment Variables](#environment-variables)
  - [Database Initialization](#database-initialization)
  - [Running the API](#running-the-api)
  - [API Overview](#api-overview)
  - [Persistence & File Layout](#persistence--file-layout)
  - [RAG Pipeline](#rag-pipeline)
- [Frontend](#frontend)
- [Development Tips](#development-tips)

## Repository structure
- `backend/`: FastAPI app, SQLAlchemy models, RAG pipeline, and services.
- `frontend/`: Vite + React interface for authentication, subject/document management, and chat.
- `app.db`: Default SQLite database created on startup.
- `database.pdf`: Reference design document.
- `test_db.py`: Utility for inspecting the SQLite file.

## Backend
### Requirements
- Python 3.10+
- [Ollama](https://ollama.com/) running locally (default host `http://localhost:11434`).
- System packages needed for PyTorch, FAISS, and transformers (see `backend/requirements.txt`).

### Setup
#### Local (virtualenv)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

#### Docker Compose
1. Create a `.env` file at the project root (see [Environment Variables](#environment-variables)); at minimum set `SECRET_KEY`.
2. Ensure Ollama is running on the host at `http://localhost:11434` so the container can reach `host.docker.internal:11434`.
3. Build and start the stack (backend + frontend):
```bash
docker compose up --build
# or run in detached mode
docker compose up -d --build
```
   - Backend: http://localhost:8000/api/v1
   - Frontend: http://localhost:5173
   - Data persists via mounted volumes: `uploads/`, `indexes/`, `app.db`, and a shared Hugging Face cache volume.

### Environment Variables
Create a `.env` file to override defaults from `backend/config.py`:
```env
DATABASE_URL=sqlite:///./app.db
SECRET_KEY=change-me
ACCESS_TOKEN_EXPIRE_MINUTES=30
UPLOAD_DIR=uploads
INDEX_DIR=indexes
EMBEDDING_MODEL=intfloat/multilingual-e5-base
LLM_MODEL=qwen2:7b
OLLAMA_BASE_URL=http://localhost:11434
TOP_K_RETRIEVE=5
SIMILARITY_THRESHOLD=0.85
BM25_THRESHOLD=0.3
RERANKER_MODEL=BAAI/bge-reranker-base
USE_RERANKER=True
```

### Database Initialization
Run once to create tables (the first command runs automatically on server start):
```bash
python -m backend.init_script          # create tables
python -m backend.init_script test     # optional: seed demo user/subject
```

### Running the API
```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### API Overview (base path `/api/v1`)
- `POST /auth/register`, `POST /auth/login/json`, `GET /auth/me`: user signup/login/profile using JWT.
- `GET/POST/PUT/DELETE /subjects`: CRUD for subjects owned by the authenticated user.
- `GET/POST /subjects/{id}/documents`: upload PDF files; each upload triggers a background rebuild of the subject’s vector store.
- `GET/DELETE /documents/{id}`: fetch or remove a document.
- `GET/POST /subjects/{id}/conversations`: list or create conversations bound to a subject and its documents.
- `GET/DELETE /conversations/{id}` and `GET /conversations/{id}/messages`: conversation details and history.
- `GET /conversations/{id}/vector-status`, `POST /conversations/{id}/rebuild-vector`: monitor or manually rebuild a subject’s vector index.
- `POST /chat` and `POST /chat/stream`: ask questions with full responses or Server-Sent Events streaming; messages are persisted per conversation.

### Persistence & File Layout
- Database: SQLite at `app.db` by default (SQLAlchemy models in `backend/models.py`).
- Uploads: `uploads/user_{user_id}/subject_{subject_id}/<filename>.pdf`.
- Vector stores (per subject): `indexes/user_{user_id}/subject_{subject_id}/subject.index` plus `subject.json` metadata; status tracked in `vector_store_meta`.

### RAG Pipeline
- **Ingestion**: PDF/TXT loaders (`langchain_community`), chunked with ~800-character chunks and 120-character overlap, storing page/chunk metadata for citations.
- **Embeddings**: `intfloat/multilingual-e5-base` (CPU by default) through `Embedder`.
- **Storage**: FAISS index plus JSON metadata managed by `VectorStore`; paths generated per subject via `vector_paths.py`.
- **Retrieval**: Hybrid semantic + BM25 search (`Retriever`) with configurable thresholds (`SIMILARITY_THRESHOLD`, `BM25_THRESHOLD`); filters document IDs for each conversation and caches retrievers per active subject to avoid disk reloads.
- **Reranking (optional)**: `BAAI/bge-reranker-base` prunes contexts before generation.
- **Prompting & Generation**: Structured prompts from `prompt_builder` enforce document-grounded answers with Markdown formatting and follow-up questions. Responses use Ollama (default `qwen2:7b`) via `generate_answer` or streaming `generate_answer_stream`.
- **Language Support**: `LanguageDetector` automatically responds in the query language when enabled.

### Requirements
- Node.js 18+.

### Setup & Development
```bash
cd frontend
npm install
npm run dev -- --host --port 5173
```

The dev server connects to `http://localhost:8000/api/v1` by default. Key features include JWT-based auth, subject/document management, upload progress modals, automatic vector status polling, and SSE-based chat with Markdown rendering. The API base URL is defined in `frontend/src/App.jsx` (`API_BASE_URL`).

## Development Tips
- Use `backend/services/rag_service.py` for debugging vector builds and retrieval; status messages are printed to stdout.
- The vector store cache (`vector_store_cache.py`) clears when switching subjects. If a build fails, check `vector_status` via the API before retrying.
- Ensure Ollama has pulled the configured model (e.g., `ollama pull qwen2:7b`) to avoid generation failures on new machines.
