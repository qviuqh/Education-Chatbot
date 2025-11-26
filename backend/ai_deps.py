"""
AI Model Dependencies
---------------------
Cung cấp các hàm singleton cho các model AI (Embedder, Reranker, Ollama client).
Các instance này được khởi tạo một lần và dùng chung cho toàn bộ ứng dụng.
"""
from functools import lru_cache
from ollama import Client

from .config import settings
from .rag_pipeline.embedder import Embedder
from .rag_pipeline.reranker import Reranker


@lru_cache(maxsize=1)
def get_embedder() -> Embedder:
    """Trả về Embedder dùng chung."""
    return Embedder(model_name=settings.EMBEDDING_MODEL)


@lru_cache(maxsize=1)
def get_reranker() -> Reranker:
    """Trả về Reranker dùng chung (tạo khi cần)."""
    return Reranker(model_name=settings.RERANKER_MODEL)


@lru_cache(maxsize=1)
def get_ollama_client() -> Client:
    """Trả về Ollama client dùng chung."""
    return Client(host=settings.OLLAMA_BASE_URL)


def warmup_ai_models() -> None:
    """Khởi tạo sẵn các model AI khi server start."""
    get_embedder()
    if settings.USE_RERANKER:
        get_reranker()
    get_ollama_client()