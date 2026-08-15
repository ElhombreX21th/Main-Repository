from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.db.session import get_db
from app.models.entities import Organization, RefreshToken, User, UserRole
from app.schemas.auth import RefreshRequest, RegisterRequest, Token

router = APIRouter(prefix="/auth", tags=["auth"])


def issue_token_pair(db: Session, user: User) -> Token:
    raw, digest, expires = create_refresh_token()
    db.add(RefreshToken(user_id=user.id, token_hash=digest, expires_at=expires))
    db.commit()
    return Token(access_token=create_access_token(str(user.id)), refresh_token=raw)


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    if db.scalar(select(User.id).where(User.email == data.email.lower())):
        raise HTTPException(status.HTTP_409_CONFLICT, "E-mail já cadastrado")
    organization = Organization(name=data.organization_name, country_code=data.country_code.upper())
    db.add(organization)
    db.flush()
    user = User(
        organization_id=organization.id,
        email=data.email.lower(),
        password_hash=hash_password(data.password),
        role=UserRole.admin,
    )
    db.add(user)
    db.commit()
    return issue_token_pair(db, user)


@router.post("/token", response_model=Token)
def token(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == form.username.lower()))
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenciais inválidas")
    return issue_token_pair(db, user)


@router.post("/refresh", response_model=Token)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    stored = db.scalar(
        select(RefreshToken)
        .where(RefreshToken.token_hash == hash_token(payload.refresh_token))
        .with_for_update()
    )
    now = datetime.now(UTC)
    if not stored or stored.revoked_at or stored.expires_at.replace(tzinfo=UTC) <= now:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token inválido")
    user = db.get(User, stored.user_id)
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuário inválido")
    stored.revoked_at = now
    db.commit()
    return issue_token_pair(db, user)
