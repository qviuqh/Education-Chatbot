"""
AI Model Dependencies
---------------------
Cung cấp các hàm singleton cho các model AI (Embedder, Reranker, Ollama client).
Các instance này được khởi tạo một lần và dùng chung cho toàn bộ ứng dụng.
"""
import ollama
from functools import lru_cache
from ollama import Client

from .config import settings
from .rag_pipeline.embedder import Embedder
from .rag_pipeline.reranker import Reranker


@lru_cache(maxsize=1)
def get_embedder() -> Embedder:
    """
    Trả về Embedder dùng chung.
    LƯU Ý: Chạy trên CPU để dành VRAM cho Ollama (Generator)
    """
    embedder = Embedder(model_name=settings.EMBEDDING_MODEL, device="cpu")
    print("✅ Đã tải xong model Embedding.", flush=True)
    return embedder


@lru_cache(maxsize=1)
def get_reranker() -> Reranker:
    """
    Trả về Reranker dùng chung (tạo khi cần).
    LƯU Ý: Chạy trên CPU để dành VRAM cho Ollama (Generator)
    """
    # Reranker class của bạn đã có logic nhận tham số device (xem file reranker.py cũ)
    reranker = Reranker(model_name=settings.RERANKER_MODEL, device="cpu")
    print("✅ Đã tải xong model Reranker.", flush=True)
    return reranker


@lru_cache(maxsize=1)
def get_ollama_client() -> Client:
    """Trả về Ollama client dùng chung."""
    return Client(host=settings.OLLAMA_BASE_URL)

def warmup_ai_models() -> None:
    """Khởi tạo sẵn các model AI khi server start."""
    print("WARMUP: Initializing models on CPU to save VRAM for Ollama...")
    get_embedder()
    if settings.USE_RERANKER:
        get_reranker()
    get_ollama_client()