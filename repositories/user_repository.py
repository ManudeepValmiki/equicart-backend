from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from models.user_model import User
from schemas.user_schema import UserCreate, UserUpdate
from utils.password_handler import hash_password


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 20) -> List[User]:
        result = await self.db.execute(select(User).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def create(self, data: UserCreate) -> User:
        user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            phone_number=data.phone_number,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def update(self, user_id: UUID, data: UserUpdate) -> Optional[User]:
        values = data.model_dump(exclude_none=True)
        if not values:
            return await self.get_by_id(user_id)
        await self.db.execute(
            update(User).where(User.id == user_id).values(**values)
        )
        return await self.get_by_id(user_id)

    async def update_password(self, user_id: UUID, new_password: str) -> None:
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(hashed_password=hash_password(new_password))
        )

    async def deactivate(self, user_id: UUID) -> None:
        await self.db.execute(
            update(User).where(User.id == user_id).values(is_active=False)
        )

    async def verify(self, user_id: UUID) -> None:
        await self.db.execute(
            update(User).where(User.id == user_id).values(is_verified=True)
        )
