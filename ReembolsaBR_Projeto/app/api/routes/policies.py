from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user, require_roles
from app.db.session import get_db
from app.models.entities import Policy, User, UserRole
from app.schemas.policy import PolicyCreate, PolicyRead
from app.services.audit import audit_async

router = APIRouter(prefix="/policies", tags=["policies"])


@router.get("", response_model=list[PolicyRead])
async def list_policies(user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Policy).where(Policy.organization_id == user.organization_id))
    return list(result.scalars().all())


@router.post("", response_model=PolicyRead, status_code=status.HTTP_201_CREATED)
async def create_policy(
    payload: PolicyCreate,
    user: User = Depends(require_roles(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
):
    policy = Policy(organization_id=user.organization_id, **payload.model_dump())
    db.add(policy)
    await db.flush()
    await audit_async(db, user, "policy", policy.id, "created")
    await db.commit()
    await db.refresh(policy)
    return policy
