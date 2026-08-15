from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.db.session import get_db
from app.models.entities import AuditLog, Expense, User
from app.services.audit import audit

router = APIRouter(prefix="/privacy", tags=["privacy"])


@router.get("/me/export")
def export_personal_data(user: User = Depends(current_user), db: Session = Depends(get_db)):
    expenses = list(db.scalars(select(Expense).where(Expense.user_id == user.id)))
    logs = list(db.scalars(select(AuditLog).where(AuditLog.actor_id == user.id)))
    return {
        "user": {"id": str(user.id), "email": user.email, "role": user.role.value},
        "expenses": [
            {
                "id": str(item.id),
                "amount": str(item.amount),
                "currency": item.currency,
                "date": item.expense_date.isoformat(),
                "status": item.status.value,
            }
            for item in expenses
        ],
        "audit_actions": [item.action for item in logs],
    }


@router.delete("/me", status_code=204)
def anonymize_personal_data(user: User = Depends(current_user), db: Session = Depends(get_db)):
    audit(db, user, "user", user.id, "anonymized")
    user.email = f"deleted-{user.id}@invalid.local"
    user.password_hash = "!anonymized"
    user.is_active = False
    db.commit()
