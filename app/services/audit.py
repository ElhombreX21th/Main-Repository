import uuid

from sqlalchemy.orm import Session

from app.models.entities import AuditLog, User


def audit(
    db: Session, actor: User, entity_type: str, entity_id: uuid.UUID, action: str, details=None
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
