"""
Conversations API - Quản lý conversations
"""
from fastapi import APIRouter, Depends, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

import schemas
import models
from db import get_db
from deps import get_current_user, get_user_conversation
from services import conversation_service, rag_service

router = APIRouter(tags=["Conversations"])


@router.get("/subjects/{subject_id}/conversations", response_model=List[schemas.ConversationRead])
def list_conversations(
    subject_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lấy tất cả conversations của môn học
    """
    conversations = conversation_service.get_user_conversations(
        db,
        current_user.id,
        subject_id
    )
    return conversations


@router.post(
    "/subjects/{subject_id}/conversations",
    response_model=schemas.ConversationRead,
    status_code=status.HTTP_201_CREATED
)
def create_conversation(
    subject_id: int,
    conversation_data: schemas.ConversationCreate,
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Tạo conversation mới và build vector store
    """
    # Verify subject_id matches
    if conversation_data.subject_id != subject_id:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subject ID mismatch"
        )
    
    # Tạo conversation
    conversation = conversation_service.create_conversation(
        db,
        current_user.id,
        conversation_data
    )
    
    # Build vector store trong background
    background_tasks.add_task(
        rag_service.build_vector_store_for_conversation,
        db,
        conversation.id
    )
    
    return conversation


@router.get("/conversations/{conversation_id}", response_model=schemas.ConversationDetail)
def get_conversation(
    conversation_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lấy thông tin chi tiết conversation
    """
    conversation = conversation_service.get_conversation_by_id(
        db,
        conversation_id,
        current_user.id
    )
    
    # Lấy documents
    documents = [conv_doc.document for conv_doc in conversation.documents]
    
    # Lấy vector store status
    vector_status = None
    if conversation.vector_store_meta:
        vector_status = conversation.vector_store_meta.status
    
    return {
        **conversation.__dict__,
        "documents": documents,
        "vector_store_status": vector_status
    }


@router.get("/conversations/{conversation_id}/messages", response_model=List[schemas.MessageRead])
def get_conversation_messages(
    conversation_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lấy tất cả messages trong conversation
    """
    messages = conversation_service.get_conversation_messages(
        db,
        conversation_id,
        current_user.id
    )
    return messages


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Xóa conversation
    """
    conversation_service.delete_conversation(db, conversation_id, current_user.id)
    return None


@router.get("/conversations/{conversation_id}/vector-status", response_model=schemas.VectorStoreStatus)
def get_vector_store_status(
    conversation_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lấy trạng thái vector store
    """
    # Verify ownership
    conversation_service.get_conversation_by_id(db, conversation_id, current_user.id)
    
    vector_meta = rag_service.get_vector_store_status(db, conversation_id)
    return vector_meta


@router.post("/conversations/{conversation_id}/rebuild-vector", status_code=status.HTTP_202_ACCEPTED)
def rebuild_vector_store(
    conversation_id: int,
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Rebuild vector store cho conversation
    """
    # Verify ownership
    conversation_service.get_conversation_by_id(db, conversation_id, current_user.id)
    
    # Rebuild trong background
    background_tasks.add_task(
        rag_service.build_vector_store_for_conversation,
        db,
        conversation_id
    )
    
    return {"message": "Vector store rebuild started"}
