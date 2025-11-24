"""
Main FastAPI Application
Entry point của backend
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config import settings
from .db import init_db

# Import routers
from .api import auth, subjects, documents, conversations, chat


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events - chạy khi app startup và shutdown
    """
    # Startup: Tạo database tables
    print("🚀 Starting application...")
    init_db()
    print("✅ Database initialized")
    
    yield
    
    # Shutdown
    print("👋 Shutting down application...")


# Khởi tạo FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="RAG-based Learning Assistant API",
    version="1.0.0",
    lifespan=lifespan
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(subjects.router, prefix=settings.API_V1_PREFIX)
app.include_router(documents.router, prefix=settings.API_V1_PREFIX)
app.include_router(conversations.router, prefix=settings.API_V1_PREFIX)
app.include_router(chat.router, prefix=settings.API_V1_PREFIX)


@app.get("/")
def root():
    """
    Health check endpoint
    """
    return {
        "message": "RAG Learning Assistant API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
def health_check():
    """
    Health check cho monitoring
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
