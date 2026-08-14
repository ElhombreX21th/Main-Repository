from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.entities import AuditLog, User, UserRole


class AuditRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str
    action: str
    details: str | None


router = APIRouter(prefix="/audit-logs", tags=["audit"])


@router.get("", response_model=list[AuditRead])
def list_audit(user: User = Depends(require_roles(UserRole.admin)), db: Session = Depends(get_db)):
    return list(
        db.scalars(
            select(AuditLog)
            .where(AuditLog.organization_id == user.organization_id)
            .order_by(AuditLog.created_at.desc())
        )
    )
