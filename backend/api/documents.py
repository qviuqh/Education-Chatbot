"""
Documents API - Upload và quản lý tài liệu
"""
from fastapi import APIRouter, Depends, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List

from .. import schemas, models
from ..db import get_db
from ..deps import get_current_user, get_user_subject
from ..services import document_service

router = APIRouter(tags=["Documents"])


@router.get("/subjects/{subject_id}/documents", response_model=List[schemas.DocumentRead])
def list_documents(
    subject_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lấy tất cả tài liệu của môn học
    """
    documents = document_service.get_subject_documents(
        db,
        subject_id,
        current_user.id
    )
    return documents


@router.post(
    "/subjects/{subject_id}/documents",
    response_model=schemas.DocumentRead,
    status_code=status.HTTP_201_CREATED
)
def upload_document(
    subject_id: int,
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload tài liệu PDF
    """
    document = document_service.save_uploaded_file(
        db,
        subject_id,
        current_user.id,
        file
    )
    return document


@router.get("/documents/{document_id}", response_model=schemas.DocumentRead)
def get_document(
    document_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lấy thông tin một tài liệu
    """
    document = document_service.get_document_by_id(
        db,
        document_id,
        current_user.id
    )
    return document


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Xóa tài liệu
    """
    document_service.delete_document(db, document_id, current_user.id)
    return None
