import re
from typing import Union

from fastapi import HTTPException, status
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Expense, ExpenseStatus, Policy, User
from app.schemas.expense import ExpenseCreate
from app.services.audit import audit_async


def normalized(value: str | None) -> str | None:
    return re.sub(r"\D", "", value) if value else None


async def create_expense_async(db: AsyncSession, actor: User, data: ExpenseCreate) -> Expense:
    values = data.model_dump()
    values["merchant_tax_id"] = normalized(data.merchant_tax_id)
    values["invoice_key"] = normalized(data.invoice_key)
    duplicate_terms = []
    if values["invoice_key"]:
        duplicate_terms.append(Expense.invoice_key == values["invoice_key"])
    if values["merchant_tax_id"]:
        duplicate_terms.append(
            and_(
                Expense.merchant_tax_id == values["merchant_tax_id"],
                Expense.expense_date == data.expense_date,
                Expense.amount == data.amount,
            )
        )
    if duplicate_terms:
        result = await db.execute(
            select(Expense.id).where(
                Expense.organization_id == actor.organization_id, or_(*duplicate_terms)
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(status.HTTP_409_CONFLICT, "Despesa duplicada")

    result = await db.execute(
        select(Policy).where(
            Policy.organization_id == actor.organization_id,
            Policy.category == data.category,
            Policy.country_code == data.country_code.upper(),
        )
    )
    policy = result.scalar_one_or_none()
    violation = None
    if policy and (policy.currency != data.currency.upper() or data.amount > policy.max_amount):
        violation = f"Limite: {policy.currency} {policy.max_amount}"
    expense = Expense(
        **values,
        organization_id=actor.organization_id,
        user_id=actor.id,
        currency=data.currency.upper(),
        country_code=data.country_code.upper(),
        policy_violation=violation,
    )
    db.add(expense)
    await db.flush()
    await audit_async(db, actor, "expense", expense.id, "created", violation)
    await db.commit()
    await db.refresh(expense)
    return expense


TRANSITIONS = {
    "submit": ({ExpenseStatus.draft, ExpenseStatus.rejected}, ExpenseStatus.submitted),
    "approve": ({ExpenseStatus.submitted}, ExpenseStatus.approved),
    "reject": ({ExpenseStatus.submitted}, ExpenseStatus.rejected),
    "reimburse": ({ExpenseStatus.approved}, ExpenseStatus.reimbursed),
}


async def transition_async(db: AsyncSession, actor: User, expense: Expense, action: str) -> Expense:
    allowed, target = TRANSITIONS[action]
    if expense.status not in allowed:
        raise HTTPException(status.HTTP_409_CONFLICT, "Transição de status inválida")
    expense.status = target
    await audit_async(db, actor, "expense", expense.id, action)
    await db.commit()
    await db.refresh(expense)
    return expense
