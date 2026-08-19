from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.entities import Organization, User, UserRole
from app.schemas.auth import RegisterRequest, Token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User.id).where(User.email == data.email.lower()))
    if result.scalar_one_or_none():
        raise HTTPException(status.HTTP_409_CONFLICT, "E-mail já cadastrado")
    organization = Organization(name=data.organization_name, country_code=data.country_code.upper())
    db.add(organization)
    await db.flush()
    user = User(
        organization_id=organization.id,
        email=data.email.lower(),
        password_hash=hash_password(data.password),
        role=UserRole.admin,
    )
    db.add(user)
    await db.commit()
    return Token(access_token=create_access_token(str(user.id)))


@router.post("/token", response_model=Token)
async def token(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == form.username.lower()))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenciais inválidas")
    return Token(access_token=create_access_token(str(user.id)))
