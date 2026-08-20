import re

from fastapi import HTTPException, status
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.models.entities import Expense, ExpenseStatus, Policy, User
from app.schemas.expense import ExpenseCreate
from app.services.audit import audit


def normalized(value: str | None) -> str | None:
    return re.sub(r"\D", "", value) if value else None


def create_expense(db: Session, actor: User, data: ExpenseCreate) -> Expense:
    values = data.model_dump()
    values["category"] = data.category.strip()
    values["merchant_tax_id"] = normalized(data.merchant_tax_id)
    values["merchant_state"] = data.merchant_state.upper() if data.merchant_state else None
    values["invoice_key"] = normalized(data.invoice_key)
    values["currency"] = data.currency.upper()
    values["country_code"] = data.country_code.upper()
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
    if duplicate_terms and db.scalar(
        select(Expense.id).where(
            Expense.organization_id == actor.organization_id, or_(*duplicate_terms)
        )
    ):
        raise HTTPException(status.HTTP_409_CONFLICT, "Esta despesa já foi registrada.")

    policy = db.scalar(
        select(Policy).where(
            Policy.organization_id == actor.organization_id,
            Policy.category == values["category"],
            Policy.country_code == values["country_code"],
        )
    )
    violation = None
    if policy and (policy.currency != values["currency"] or data.amount > policy.max_amount):
        violation = f"Limite: {policy.currency} {policy.max_amount}"
    expense = Expense(
        **values,
        organization_id=actor.organization_id,
        user_id=actor.id,
        policy_violation=violation,
    )
    db.add(expense)
    db.flush()
    audit(db, actor, "expense", expense.id, "created", violation)
    db.commit()
    db.refresh(expense)
    return expense


TRANSITIONS = {
    "submit": ({ExpenseStatus.draft, ExpenseStatus.rejected}, ExpenseStatus.submitted),
    "approve": ({ExpenseStatus.submitted}, ExpenseStatus.approved),
    "reject": ({ExpenseStatus.submitted}, ExpenseStatus.rejected),
    "reimburse": ({ExpenseStatus.approved}, ExpenseStatus.reimbursed),
}


def transition(db: Session, actor: User, expense: Expense, action: str) -> Expense:
    allowed, target = TRANSITIONS[action]
    if expense.status not in allowed:
        raise HTTPException(status.HTTP_409_CONFLICT, "A mudança de status não é permitida.")
    expense.status = target
    audit(db, actor, "expense", expense.id, action)
    db.commit()
    db.refresh(expense)
    return expense
