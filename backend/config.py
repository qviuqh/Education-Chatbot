from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./app.db"
    
    # JWT
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
    BACKEND_CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]
    
    # Embedder Settings
    EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    EMBEDDING_DIMENSION: int = 384
    
    # LLM Settings
    LLM_MODEL: str = "gpt-3.5-turbo"  # Hoặc model khác bạn dùng
    LLM_API_KEY: str = ""  # Đọc từ .env
    
    # Retriever Settings
    TOP_K_RETRIEVE: int = 5
    SIMILARITY_THRESHOLD: float = 0.3
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Khởi tạo settings
settings = Settings()

# Tạo thư mục nếu chưa có
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.INDEX_DIR).mkdir(parents=True, exist_ok=True)
