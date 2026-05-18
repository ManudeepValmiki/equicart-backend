from fastapi import Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import get_db
from repositories.user_repository import UserRepository
from utils.jwt_handler import decode_token
from exceptions.custom_exception import UnauthorizedException, ForbiddenException
from models.user_model import User, UserRole

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Dependency: extract and validate the JWT, return the authenticated user."""
    if not credentials:
        raise UnauthorizedException(detail="Authorization header missing")

    payload = decode_token(credentials.credentials)
    user_id: str = payload.get("sub")
    if not user_id:
        raise UnauthorizedException(detail="Invalid token payload")

    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user:
        raise UnauthorizedException(detail="User not found")
    if not user.is_active:
        raise UnauthorizedException(detail="Account is deactivated")

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency: ensure the user is active (alias for clarity in routes)."""
    return current_user


def require_role(*roles: UserRole):
    """Dependency factory: restrict access to users with specific roles."""

    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise ForbiddenException(
                detail=f"Access requires one of the following roles: {[r.value for r in roles]}"
            )
        return current_user

    return role_checker


# Convenience role dependencies
require_admin = require_role(UserRole.ADMIN)
require_seller = require_role(UserRole.ADMIN, UserRole.SELLER)
