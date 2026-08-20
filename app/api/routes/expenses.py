import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_user, require_roles
from app.db.session import get_db
from app.models.entities import Expense, User, UserRole
from app.parsers import parse_br_receipt
from app.schemas.expense import ExpenseCreate, ExpenseRead, ParsedReceipt, ReceiptText
from app.services.expenses import create_expense, transition

router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.post("/parse-receipt", response_model=ParsedReceipt)
def parse_receipt(payload: ReceiptText, _: User = Depends(current_user)):
    return parse_br_receipt(payload.text)


@router.post("", response_model=ExpenseRead, status_code=status.HTTP_201_CREATED)
def create(
    payload: ExpenseCreate, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    return create_expense(db, user, payload)


@router.get("", response_model=list[ExpenseRead])
def list_expenses(user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = select(Expense).where(Expense.organization_id == user.organization_id)
    if user.role == UserRole.employee:
        query = query.where(Expense.user_id == user.id)
    return list(db.scalars(query.order_by(Expense.created_at.desc())))


def tenant_expense(expense_id: uuid.UUID, user: User, db: Session) -> Expense:
    expense = db.scalar(
        select(Expense).where(
            Expense.id == expense_id, Expense.organization_id == user.organization_id
        )
    )
    if not expense:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Despesa não encontrada.")
    return expense


@router.post("/{expense_id}/submit", response_model=ExpenseRead)
def submit(
    expense_id: uuid.UUID, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    expense = tenant_expense(expense_id, user, db)
    if expense.user_id != user.id and user.role != UserRole.admin:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Apenas o responsável pela despesa pode enviá-la.",
        )
    return transition(db, user, expense, "submit")


def workflow_route(action: str):
    def route(
        expense_id: uuid.UUID,
        user: User = Depends(require_roles(UserRole.approver, UserRole.admin)),
        db: Session = Depends(get_db),
    ):
        return transition(db, user, tenant_expense(expense_id, user, db), action)

    return route


for action in ("approve", "reject", "reimburse"):
    router.add_api_route(
        f"/{{expense_id}}/{action}",
        workflow_route(action),
        methods=["POST"],
        response_model=ExpenseRead,
    )
