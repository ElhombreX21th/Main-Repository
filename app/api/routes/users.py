from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.security import hash_password
from app.db.session import get_db
from app.models.entities import User, UserRole
from app.schemas.user import UserCreate, UserRead
from app.services.audit import audit

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    admin: User = Depends(require_roles(UserRole.admin)),
    db: Session = Depends(get_db),
):
    if payload.role not in {UserRole.employee, UserRole.approver}:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Administradores só podem criar usuários employee ou approver",
        )

    user = User(
        organization_id=admin.organization_id,
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    try:
        db.add(user)
        db.flush()
        audit(db, admin, "user", user.id, "created", f"role={user.role.value}")
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "E-mail já cadastrado") from exc
    db.refresh(user)
    return user
