# Education Chatbot

A full-stack Retrieval-Augmented Generation (RAG) learning assistant. The backend uses FastAPI with a hybrid FAISS + BM25 retriever, optional reranking, and Ollama generation; the frontend is a Vite/React dashboard for uploading study materials and chatting with grounded answers.

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
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

Create a `.env` file if you need to override defaults from `backend/config.py`:
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

a) Initialize the database (runs automatically on server startup):
```bash
python -m backend.init_script          # create tables
python -m backend.init_script test     # optional: seed demo user/subject
```

b) Start the API server:
```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### API overview (base path `/api/v1`)
- `POST /auth/register`, `POST /auth/login/json`, `GET /auth/me`: user signup/login/profile using JWT.
- `GET/POST/PUT/DELETE /subjects`: CRUD for subjects owned by the authenticated user.
- `GET/POST /subjects/{id}/documents`: upload PDF files (unique-named and stored under `uploads/user_{id}/subject_{id}`); triggers background rebuild of that subject’s vector store.
- `GET/DELETE /documents/{id}`: fetch or remove a document.
- `GET/POST /subjects/{id}/conversations`: list or create conversations bound to a subject and its documents.
- `GET/DELETE /conversations/{id}` plus `GET /conversations/{id}/messages`: conversation details and history.
- `GET /conversations/{id}/vector-status`, `POST /conversations/{id}/rebuild-vector`: monitor or manually rebuild the vector index for a subject.
- `POST /chat` and `POST /chat/stream`: ask questions with full response or Server-Sent Events streaming; messages are persisted per conversation.

### Persistence and file layout
- Database: SQLite at `app.db` by default (SQLAlchemy models in `backend/models.py`).
- Uploads: `uploads/user_{user_id}/subject_{subject_id}/<filename>.pdf`.
- Vector stores (per subject): `indexes/user_{user_id}/subject_{subject_id}/subject.index` + `subject.json` with metadata; status tracked in `vector_store_meta`.

## RAG pipeline
- **Ingestion**: PDF/TXT loaders (`langchain_community`), chunked via `chunk_documents` with 800-character chunks and 120-character overlap, storing page/chunk metadata for citations.
- **Embeddings**: `intfloat/multilingual-e5-base` (CPU by default) through `Embedder`.
- **Storage**: FAISS index plus JSON metadata managed by `VectorStore`; paths generated per subject via `vector_paths.py`.
- **Retrieval**: Hybrid semantic + BM25 search (`Retriever`) with thresholds (`SIMILARITY_THRESHOLD`, `BM25_THRESHOLD`); filters allowed document IDs for each conversation; caches retrievers per active subject to avoid disk reloads.
- **Reranking** (optional): `BAAI/bge-reranker-base` to keep top contexts before generation.
- **Prompting & generation**: Structured prompt from `prompt_builder` enforces “document-only” answers with Markdown formatting and follow-up questions. Responses are produced by Ollama (default `qwen2:7b`) via `generate_answer` or streaming `generate_answer_stream`.
- **Language support**: `LanguageDetector` auto-selects the response language to match the query when enabled.

## Frontend
- Requirements: Node.js 18+.
- Install dependencies:
```bash
cd frontend
npm install
```
- Run the dev server (connects to `http://localhost:8000/api/v1` by default):
```bash
npm run dev -- --host --port 5173
```

Features include JWT-based login/register, subject and document management, upload progress modals, automatic vector status polling, and SSE-based chat with markdown rendering. API base URL is defined in `frontend/src/App.jsx` (`API_BASE_URL`).

## Development tips
- Use `backend/services/rag_service.py` for debugging vector builds and retrieval—status messages are printed to stdout.
- The vector store cache (`vector_store_cache.py`) clears when switching subjects; if a build fails, check `vector_status` via the API before retrying.
- When running on a fresh machine, ensure Ollama has pulled the configured model (e.g., `ollama pull qwen2:7b`) to avoid generation failures.
