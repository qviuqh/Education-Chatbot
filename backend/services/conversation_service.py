from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List

from .. import models, schemas


def create_conversation(
    db: Session,
    user_id: int,
    conversation_data: schemas.ConversationCreate
) -> models.Conversation:
    """
    Tạo conversation mới
    """
    # Kiểm tra subject thuộc về user
    subject = db.query(models.Subject).filter(
        models.Subject.id == conversation_data.subject_id,
        models.Subject.user_id == user_id
    ).first()
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    # Kiểm tra documents thuộc về subject
    documents = db.query(models.Document).filter(
        models.Document.id.in_(conversation_data.document_ids),
        models.Document.subject_id == conversation_data.subject_id
    ).all()
    
    if len(documents) != len(conversation_data.document_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Some documents not found or don't belong to this subject"
        )
    
    # Tạo conversation
    db_conversation = models.Conversation(
        user_id=user_id,
        subject_id=conversation_data.subject_id,
        title=conversation_data.title
    )
    
    db.add(db_conversation)
    db.flush()  # Để có conversation.id
    
    # Liên kết documents
    for doc in documents:
        conv_doc = models.ConversationDocument(
            conversation_id=db_conversation.id,
            document_id=doc.id
        )
        db.add(conv_doc)
    
    db.commit()
    db.refresh(db_conversation)
    
    return db_conversation


def get_user_conversations(
    db: Session,
    user_id: int,
    subject_id: int = None
) -> List[models.Conversation]:
    """
    Lấy tất cả conversations của user
    """
    query = db.query(models.Conversation).filter(
        models.Conversation.user_id == user_id
    )
    
    if subject_id:
        query = query.filter(models.Conversation.subject_id == subject_id)
    
    conversations = query.order_by(
        models.Conversation.updated_at.desc()
    ).all()
    
    return conversations


def get_conversation_by_id(
    db: Session,
    conversation_id: int,
    user_id: int
) -> models.Conversation:
    """
    Lấy conversation theo ID và kiểm tra quyền
    """
    conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id,
        models.Conversation.user_id == user_id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    return conversation


def get_conversation_messages(
    db: Session,
    conversation_id: int,
    user_id: int
) -> List[models.Message]:
    """
    Lấy tất cả messages trong conversation
    """
    # Kiểm tra quyền
    get_conversation_by_id(db, conversation_id, user_id)
    
    messages = db.query(models.Message).filter(
        models.Message.conversation_id == conversation_id
    ).order_by(models.Message.created_at.asc()).all()
    
    return messages


def save_message(
    db: Session,
    conversation_id: int,
    role: str,
    content: str
) -> models.Message:
    """
    Lưu message mới
    """
    message = models.Message(
        conversation_id=conversation_id,
        role=role,
        content=content
    )
    
    db.add(message)
    db.commit()
    db.refresh(message)
    
    return message


def delete_conversation(db: Session, conversation_id: int, user_id: int) -> None:
    """
    Xóa conversation
    """
    conversation = get_conversation_by_id(db, conversation_id, user_id)
    
    db.delete(conversation)
    db.commit()
