from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.entities import Expense, ExpenseStatus, User, UserRole

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("/erp/approved-expenses")
def export_approved_expenses(
    user: User = Depends(require_roles(UserRole.admin)), db: Session = Depends(get_db)
):
    expenses = db.scalars(
        select(Expense).where(
            Expense.organization_id == user.organization_id,
            Expense.status == ExpenseStatus.approved,
        )
    )
    return {
        "organization_id": str(user.organization_id),
        "entries": [
            {
                "external_id": str(item.id),
                "account": item.category,
                "cost_center": item.cost_center,
                "amount": str(item.amount),
                "currency": item.currency,
                "document_date": item.expense_date.isoformat(),
            }
            for item in expenses
        ],
    }
