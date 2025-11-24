from sqlalchemy.orm import Session
from fastapi import HTTPException, status, UploadFile
from pathlib import Path
from typing import List
import shutil
import os

from .. import models
from ..config import settings


def get_upload_path(user_id: int, subject_id: int) -> Path:
    """
    Tạo đường dẫn lưu file
    """
    upload_path = Path(settings.UPLOAD_DIR) / f"user_{user_id}" / f"subject_{subject_id}"
    upload_path.mkdir(parents=True, exist_ok=True)
    return upload_path


def save_uploaded_file(
    db: Session,
    subject_id: int,
    user_id: int,
    file: UploadFile
) -> models.Document:
    """
    Lưu file PDF và tạo record Document
    """
    # Kiểm tra file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )
    
    # Kiểm tra subject tồn tại và thuộc về user
    subject = db.query(models.Subject).filter(
        models.Subject.id == subject_id,
        models.Subject.user_id == user_id
    ).first()
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    # Tạo đường dẫn
    upload_path = get_upload_path(user_id, subject_id)
    
    # Tạo tên file unique
    base_name = Path(file.filename).stem
    extension = Path(file.filename).suffix
    file_path = upload_path / file.filename
    
    counter = 1
    while file_path.exists():
        file_path = upload_path / f"{base_name}_{counter}{extension}"
        counter += 1
    
    # Lưu file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        file_size = os.path.getsize(file_path)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    
    # Tạo Document record
    db_document = models.Document(
        subject_id=subject_id,
        filename=file.filename,
        filepath=str(file_path),
        file_size=file_size,
        status="uploaded"
    )
    
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    
    return db_document


def get_subject_documents(
    db: Session,
    subject_id: int,
    user_id: int
) -> List[models.Document]:
    """
    Lấy tất cả tài liệu của môn học
    """
    # Kiểm tra quyền
    subject = db.query(models.Subject).filter(
        models.Subject.id == subject_id,
        models.Subject.user_id == user_id
    ).first()
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    documents = db.query(models.Document).filter(
        models.Document.subject_id == subject_id
    ).order_by(models.Document.created_at.desc()).all()
    
    return documents


def get_document_by_id(
    db: Session,
    document_id: int,
    user_id: int
) -> models.Document:
    """
    Lấy document theo ID và kiểm tra quyền
    """
    document = db.query(models.Document).join(
        models.Subject
    ).filter(
        models.Document.id == document_id,
        models.Subject.user_id == user_id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return document


def delete_document(db: Session, document_id: int, user_id: int) -> None:
    """
    Xóa document
    """
    document = get_document_by_id(db, document_id, user_id)
    
    # Xóa file vật lý
    try:
        if os.path.exists(document.filepath):
            os.remove(document.filepath)
    except Exception as e:
        print(f"Failed to delete file: {e}")
    
    # Xóa record
    db.delete(document)
    db.commit()
