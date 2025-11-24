from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List

from .. import models, schemas


def create_subject(
    db: Session,
    user_id: int,
    subject_data: schemas.SubjectCreate
) -> models.Subject:
    """
    Tạo môn học mới
    """
    db_subject = models.Subject(
        user_id=user_id,
        name=subject_data.name,
        description=subject_data.description
    )
    
    db.add(db_subject)
    db.commit()
    db.refresh(db_subject)
    
    return db_subject


def get_user_subjects(db: Session, user_id: int) -> List[models.Subject]:
    """
    Lấy tất cả môn học của user
    """
    subjects = db.query(models.Subject).filter(
        models.Subject.user_id == user_id
    ).order_by(models.Subject.created_at.desc()).all()
    
    return subjects


def get_subject_by_id(
    db: Session,
    subject_id: int,
    user_id: int
) -> models.Subject:
    """
    Lấy môn học theo ID và kiểm tra quyền
    """
    subject = db.query(models.Subject).filter(
        models.Subject.id == subject_id,
        models.Subject.user_id == user_id
    ).first()
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    return subject


def update_subject(
    db: Session,
    subject_id: int,
    user_id: int,
    subject_data: schemas.SubjectUpdate
) -> models.Subject:
    """
    Cập nhật môn học
    """
    subject = get_subject_by_id(db, subject_id, user_id)
    
    if subject_data.name is not None:
        subject.name = subject_data.name
    
    if subject_data.description is not None:
        subject.description = subject_data.description
    
    db.commit()
    db.refresh(subject)
    
    return subject


def delete_subject(db: Session, subject_id: int, user_id: int) -> None:
    """
    Xóa môn học
    """
    subject = get_subject_by_id(db, subject_id, user_id)
    
    db.delete(subject)
    db.commit()
