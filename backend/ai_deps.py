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

def check_model_downloaded(model_name):
    try:
        models = ollama.list()
        for model_info in models['models']:
            if model_info['name'].startswith(model_name):
                print(f"Model '{model_name}' is downloaded.")
                return True
        print(f"Model '{model_name}' is not downloaded.")
        return False
    except Exception as e:
        print(f"Error checking models: {e}")
        return False

def warmup_ai_models() -> None:
    """Khởi tạo sẵn các model AI khi server start."""
    print("WARMUP: Initializing models on CPU to save VRAM for Ollama...")
    get_embedder()
    if settings.USE_RERANKER:
        get_reranker()
    client = get_ollama_client()
    model_name = settings.LLM_MODEL
    
    print(f"⏳ Đang kiểm tra model Ollama: {model_name}...", flush=True)
    
    if not check_model_downloaded(model_name):
        try:
            print(f"   Đang gửi lệnh pull '{model_name}' tới Ollama (có thể mất vài phút)...", flush=True)
            
            # Thực hiện pull
            progress = client.pull(model_name, stream=True)
            
            # In tiến trình đơn giản để log
            for chunk in progress:
                if chunk.get('status') == 'success':
                    print(f"   🚀 Đã tải xong layer: {chunk.get('digest', '')[:12]}...", flush=True)
            
            print(f"✅ Model Ollama '{model_name}' đã sẵn sàng!", flush=True)
            
        except Exception as e:
            print(f"❌ Lỗi khi pull model Ollama: {e}", flush=True)
            print("   Vui lòng đảm bảo container 'ollama' đang chạy và có kết nối mạng.", flush=True)