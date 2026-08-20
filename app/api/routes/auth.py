from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_user, require_roles
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.entities import Organization, User, UserRole
from app.schemas.auth import RegisterRequest, Token, UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


def token_for(user: User) -> Token:
    return Token(
        access_token=create_access_token(user.email.lower()),
        first_name=user.full_name.split()[0] if user.full_name else None,
        role=user.role,
    )


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    if db.scalar(select(User.id).where(User.email == data.email.lower())):
        raise HTTPException(status.HTTP_409_CONFLICT, "Este e-mail já está cadastrado.")
    organization_name = data.organization_name.strip()
    if db.scalar(select(Organization.id).where(Organization.name == organization_name)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Esta organização já está cadastrada.")
    organization = Organization(name=organization_name, country_code=data.country_code.upper())
    db.add(organization)
    db.flush()
    user = User(
        organization_id=organization.id,
        full_name=data.full_name.strip(),
        email=data.email.lower(),
        password_hash=hash_password(data.password),
        role=UserRole.admin,
    )
    db.add(user)
    db.commit()
    return token_for(user)


@router.post("/token", response_model=Token)
def token(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == form.username.lower()))
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "E-mail ou senha inválidos.")
    return token_for(user)


@router.get("/me", response_model=UserRead)
def me(user: User = Depends(current_user)):
    return user


@router.get("/users", response_model=list[UserRead])
def list_users(
    user: User = Depends(require_roles(UserRole.admin)),
    db: Session = Depends(get_db),
):
    return list(
        db.scalars(
            select(User)
            .where(User.organization_id == user.organization_id)
            .order_by(User.full_name)
        )
    )


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    data: UserCreate,
    actor: User = Depends(require_roles(UserRole.admin)),
    db: Session = Depends(get_db),
):
    email = data.email.lower()
    if db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Este e-mail já está cadastrado.")
    user = User(
        organization_id=actor.organization_id,
        full_name=data.full_name.strip(),
        email=email,
        password_hash=hash_password(data.password),
        role=data.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
