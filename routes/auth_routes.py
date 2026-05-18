from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import get_db
from services.auth_service import AuthService
from schemas.user_schema import UserCreate, ChangePasswordRequest
from middleware.auth_middleware import get_current_user
from models.user_model import User
from utils.response_handler import success_response, created_response
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user account."""
    service = AuthService(db)
    result = await service.register(data)
    return created_response(
        data={
            "user": result["user"].model_dump(mode="json"),
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
            "token_type": result["token_type"],
        },
        message="Registration successful",
    )


@router.post("/login")
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate and receive JWT tokens."""
    service = AuthService(db)
    result = await service.login(data.email, data.password)
    return success_response(
        data={
            "user": result["user"].model_dump(mode="json"),
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
            "token_type": result["token_type"],
        },
        message="Login successful",
    )


@router.post("/refresh")
async def refresh_tokens(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Obtain a new access/refresh token pair using a valid refresh token."""
    service = AuthService(db)
    result = await service.refresh_tokens(data.refresh_token)
    return success_response(data=result, message="Tokens refreshed")


@router.post("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change the authenticated user's password."""
    service = AuthService(db)
    await service.change_password(
        user_id=current_user.id,
        current_password=data.current_password,
        new_password=data.new_password,
    )
    return success_response(message="Password changed successfully")


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return success_response(data=current_user.__dict__)
