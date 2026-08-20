import uuid
from collections.abc import Callable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.entities import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_prefix}/auth/token")


def current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        subject = decode_access_token(token)
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido.") from exc

    user = db.scalar(select(User).where(User.email == subject.lower()))
    if not user:
        try:
            user = db.get(User, uuid.UUID(subject))
        except ValueError:
            user = None

    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuário não encontrado ou inativo.")
    return user


def require_roles(*roles: UserRole) -> Callable:
    def dependency(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Você não tem permissão para esta ação.")
        return user

    return dependency
