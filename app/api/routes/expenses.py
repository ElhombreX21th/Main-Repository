import uuid
from typing import Union

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user, require_roles
from app.db.session import get_db
from app.models.entities import Expense, User, UserRole
from app.parsers import parse_br_receipt
from app.schemas.expense import ExpenseCreate, ExpenseRead, ParsedReceipt, ReceiptText
from app.services.expenses import create_expense_async, transition_async

router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.post("/parse-receipt", response_model=ParsedReceipt)
async def parse_receipt(payload: ReceiptText, _: User = Depends(current_user)):
    return parse_br_receipt(payload.text)


@router.post("", response_model=ExpenseRead, status_code=status.HTTP_201_CREATED)
async def create(
    payload: ExpenseCreate, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)
):
    return await create_expense_async(db, user, payload)


@router.get("", response_model=list[ExpenseRead])
async def list_expenses(user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    query = select(Expense).where(Expense.organization_id == user.organization_id)
    if user.role == UserRole.employee:
        query = query.where(Expense.user_id == user.id)
    result = await db.execute(query.order_by(Expense.created_at.desc()))
    return list(result.scalars().all())


async def tenant_expense(expense_id: uuid.UUID, user: User, db: AsyncSession) -> Expense:
    result = await db.execute(
        select(Expense).where(
            Expense.id == expense_id, Expense.organization_id == user.organization_id
        )
    )
    expense = result.scalar_one_or_none()
    if not expense:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Despesa não encontrada")
    return expense


@router.post("/{expense_id}/submit", response_model=ExpenseRead)
async def submit(
    expense_id: uuid.UUID, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)
):
    expense = await tenant_expense(expense_id, user, db)
    if expense.user_id != user.id and user.role != UserRole.admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Apenas o proprietário pode enviar")
    return await transition_async(db, user, expense, "submit")


def workflow_route(action: str):
    async def route(
        expense_id: uuid.UUID,
        user: User = Depends(require_roles(UserRole.approver, UserRole.admin)),
        db: AsyncSession = Depends(get_db),
    ):
        expense = await tenant_expense(expense_id, user, db)
        return await transition_async(db, user, expense, action)

    return route


for action in ("approve", "reject", "reimburse"):
    router.add_api_route(
        f"/{{expense_id}}/{action}",
        workflow_route(action),
        methods=["POST"],
        response_model=ExpenseRead,
    )
