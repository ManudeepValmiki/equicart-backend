from sqlalchemy.ext.asyncio import AsyncSession
from schemas.user_schema import UserCreate, UserResponse
from repositories.user_repository import UserRepository
from utils.jwt_handler import create_access_token, create_refresh_token, decode_token
from utils.password_handler import verify_password
from exceptions.custom_exception import (
    ConflictException,
    UnauthorizedException,
    NotFoundException,
    BadRequestException,
)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.repo = UserRepository(db)

    async def register(self, data: UserCreate) -> dict:
        existing = await self.repo.get_by_email(data.email)
        if existing:
            raise ConflictException(detail="Email already registered")

        user = await self.repo.create(data)
        access_token = create_access_token(subject=str(user.id), extra_claims={"role": user.role})
        refresh_token = create_refresh_token(subject=str(user.id))

        return {
            "user": UserResponse.model_validate(user),
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    async def login(self, email: str, password: str) -> dict:
        user = await self.repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise UnauthorizedException(detail="Invalid email or password")
        if not user.is_active:
            raise UnauthorizedException(detail="Account is deactivated")

        access_token = create_access_token(subject=str(user.id), extra_claims={"role": user.role})
        refresh_token = create_refresh_token(subject=str(user.id))

        return {
            "user": UserResponse.model_validate(user),
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    async def refresh_tokens(self, refresh_token: str) -> dict:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise UnauthorizedException(detail="Invalid refresh token")

        user = await self.repo.get_by_id(payload["sub"])
        if not user or not user.is_active:
            raise UnauthorizedException(detail="User not found or inactive")

        access_token = create_access_token(subject=str(user.id), extra_claims={"role": user.role})
        new_refresh_token = create_refresh_token(subject=str(user.id))

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }

    async def change_password(
        self, user_id: str, current_password: str, new_password: str
    ) -> None:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise NotFoundException(detail="User not found")
        if not verify_password(current_password, user.hashed_password):
            raise BadRequestException(detail="Current password is incorrect")
        await self.repo.update_password(user_id, new_password)
