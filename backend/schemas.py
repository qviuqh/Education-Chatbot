from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List


# ============= User Schemas =============
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    id: int
    email: str
    full_name: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ============= Subject Schemas =============
class SubjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class SubjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class SubjectRead(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============= Document Schemas =============
class DocumentRead(BaseModel):
    id: int
    subject_id: int
    filename: str
    file_size: Optional[int]
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============= Conversation Schemas =============
class ConversationCreate(BaseModel):
    subject_id: int
    title: str
    document_ids: List[int] = Field(..., min_items=1)


class ConversationRead(BaseModel):
    id: int
    subject_id: int
    title: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ConversationDetail(ConversationRead):
    """Conversation với thông tin chi tiết"""
    documents: List[DocumentRead] = []
    vector_store_status: Optional[str] = None


# ============= Message Schemas =============
class MessageRead(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============= Chat Schemas =============
class ChatRequest(BaseModel):
    conversation_id: int
    question: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    answer: str
    conversation_id: int
    message_id: Optional[int] = None
    sources: Optional[List[str]] = None  # Optional: các đoạn text được dùng


# ============= Vector Store Schemas =============
class VectorStoreStatus(BaseModel):
    status: str
    doc_count: int
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True
