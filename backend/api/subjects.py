"""
Subjects API - CRUD môn học
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

import schemas
import models
from db import get_db
from deps import get_current_user, get_user_subject
from services import subject_service

router = APIRouter(prefix="/subjects", tags=["Subjects"])


@router.get("", response_model=List[schemas.SubjectRead])
def list_subjects(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lấy tất cả môn học của user
    """
    subjects = subject_service.get_user_subjects(db, current_user.id)
    return subjects


@router.post("", response_model=schemas.SubjectRead, status_code=status.HTTP_201_CREATED)
def create_subject(
    subject_data: schemas.SubjectCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Tạo môn học mới
    """
    subject = subject_service.create_subject(db, current_user.id, subject_data)
    return subject


@router.get("/{subject_id}", response_model=schemas.SubjectRead)
def get_subject(
    subject: models.Subject = Depends(get_user_subject)
):
    """
    Lấy thông tin một môn học
    """
    return subject


@router.put("/{subject_id}", response_model=schemas.SubjectRead)
def update_subject(
    subject_id: int,
    subject_data: schemas.SubjectUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cập nhật môn học
    """
    subject = subject_service.update_subject(
        db,
        subject_id,
        current_user.id,
        subject_data
    )
    return subject


@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subject(
    subject_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Xóa môn học
    """
    subject_service.delete_subject(db, subject_id, current_user.id)
    return None
