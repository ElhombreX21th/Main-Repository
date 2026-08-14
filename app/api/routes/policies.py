from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_user, require_roles
from app.db.session import get_db
from app.models.entities import Policy, User, UserRole
from app.schemas.policy import PolicyCreate, PolicyRead
from app.services.audit import audit

router = APIRouter(prefix="/policies", tags=["policies"])


@router.get("", response_model=list[PolicyRead])
def list_policies(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return list(db.scalars(select(Policy).where(Policy.organization_id == user.organization_id)))


@router.post("", response_model=PolicyRead, status_code=status.HTTP_201_CREATED)
def create_policy(
    payload: PolicyCreate,
    user: User = Depends(require_roles(UserRole.admin)),
    db: Session = Depends(get_db),
):
    policy = Policy(organization_id=user.organization_id, **payload.model_dump())
    db.add(policy)
    db.flush()
    audit(db, user, "policy", policy.id, "created")
    db.commit()
    db.refresh(policy)
    return policy
