"""
Backend Configuration
Chứa các biến cấu hình toàn hệ thống
"""
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./app.db"
    
    # # JWT
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Directories
    UPLOAD_DIR: str = "uploads"
    INDEX_DIR: str = "indexes"
    
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "RAG Learning Assistant"
    
    # CORS
    BACKEND_CORS_ORIGINS: list = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    ]
    
    # Embedder Settings (compatible with config.yaml)
    EMBEDDING_MODEL: str = "intfloat/multilingual-e5-base"
    EMBEDDING_DIMENSION: int = 768  # multilingual-e5-base dimension
    
    # LLM Settings (sử dụng Ollama như trong code của bạn)
    LLM_MODEL: str = "qwen2:7b"  # Model mặc định cho Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"  # Ollama API endpoint
    
    # Retriever Settings
    TOP_K_RETRIEVE: int = 5
    SIMILARITY_THRESHOLD: float = 0.85
    
    BM25_THRESHOLD: float = 0.3
    
    # Reranker Settings (compatible with config.yaml)
    RERANKER_MODEL: str = "BAAI/bge-reranker-base"
    RERANKER_SCORE: float = 0.5
    USE_RERANKER: bool = True
    
    # Generator Settings
    GENERATOR_TEMPERATURE: float = 0.1
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Khởi tạo settings
settings = Settings()

# Tạo thư mục nếu chưa có
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.INDEX_DIR).mkdir(parents=True, exist_ok=True)