"""
Auth API - Đăng ký, đăng nhập, profile
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .. import schemas, models
from ..db import get_db
from ..deps import create_access_token, get_current_user
from ..services import user_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED)
def register(
    user_data: schemas.UserCreate,
    db: Session = Depends(get_db)
):
    """
    Đăng ký user mới
    """
    user = user_service.create_user(db, user_data)
    return user


@router.post("/login", response_model=schemas.Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Đăng nhập - trả về access token
    """
    user = user_service.authenticate_user(
        db,
        email=form_data.username,  # OAuth2 form dùng 'username'
        password=form_data.password
    )
    
    # Tạo access token
    access_token = create_access_token(data={"sub": user.id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/login/json", response_model=schemas.Token)
def login_json(
    login_data: schemas.UserLogin,
    db: Session = Depends(get_db)
):
    """
    Đăng nhập với JSON body (alternative endpoint)
    """
    user = user_service.authenticate_user(
        db,
        email=login_data.email,
        password=login_data.password
    )
    
    access_token = create_access_token(data={"sub": user.id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=schemas.UserRead)
def get_current_user_profile(
    current_user: models.User = Depends(get_current_user)
):
    """
    Lấy thông tin user hiện tại
    """
    return current_user
