import uuid
from typing import Union

from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import AuditLog, User


async def audit_async(
    db: Union[Session, AsyncSession], actor: User, entity_type: str, entity_id: uuid.UUID, action: str, details=None
):
    db.add(
        AuditLog(
            organization_id=actor.organization_id,
            actor_id=actor.id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            details=details,
        )
    )
