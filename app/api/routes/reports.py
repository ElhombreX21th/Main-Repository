from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.entities import Expense, User, UserRole

router = APIRouter(prefix="/reports", tags=["reports"])


class ExpenseSummary(BaseModel):
    category: str
    currency: str
    count: int
    total: Decimal


@router.get("/expenses", response_model=list[ExpenseSummary])
def expense_report(
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
    user: User = Depends(require_roles(UserRole.approver, UserRole.admin)),
    db: Session = Depends(get_db),
):
    query = (
        select(
            Expense.category,
            Expense.currency,
            func.count(Expense.id).label("count"),
            func.sum(Expense.amount).label("total"),
        )
        .where(Expense.organization_id == user.organization_id)
        .group_by(Expense.category, Expense.currency)
    )
    if start:
        query = query.where(Expense.expense_date >= start)
    if end:
        query = query.where(Expense.expense_date <= end)
    return [ExpenseSummary(**row._mapping) for row in db.execute(query)]
