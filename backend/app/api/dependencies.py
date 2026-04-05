from __future__ import annotations

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_token, security
from app.db.session import get_db
from app.modules.users.serializers import user_is_admin
from app.modules.users.models.user import User
from app.modules.users.repository import UserRepository


async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Dependency that returns the current User ORM object."""
    if creds is None:
        raise UnauthorizedError("Not authenticated")
    
    # decode_token already checks for the 'access' type by default
    user_id = decode_token(creds.credentials, expected_type="access")
    if user_id is None:
        raise UnauthorizedError("Invalid or expired access token")

    user = await UserRepository.get_active_by_id(db, user_id)
    if user is None:
        raise UnauthorizedError("User not found")

    return user


async def require_admin_user(
    user: User = Depends(get_current_user),
) -> User:
    if not user_is_admin(user):
        raise ForbiddenError("Admin access is required")
    return user
