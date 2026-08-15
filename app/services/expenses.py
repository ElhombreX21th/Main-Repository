import re
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import and_, delete, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.entities import Approval, ApprovalDecision, Expense, ExpenseStatus, Policy, User
from app.schemas.expense import ExpenseCreate
from app.services.audit import audit


def normalized(value: str | None) -> str | None:
    return re.sub(r"\D", "", value) if value else None


def create_expense(db: Session, actor: User, data: ExpenseCreate) -> Expense:
    values = data.model_dump()
    values["merchant_tax_id"] = normalized(data.merchant_tax_id)
    values["invoice_key"] = normalized(data.invoice_key)
    # These fields are supplied canonically below, so do not pass them twice.
    values.pop("currency")
    values.pop("country_code")
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
        raise HTTPException(status.HTTP_409_CONFLICT, "Despesa duplicada")

    policy = db.scalar(
        select(Policy).where(
            Policy.organization_id == actor.organization_id,
            Policy.category == data.category,
            Policy.country_code == data.country_code.upper(),
        )
    )
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
    try:
        db.add(expense)
        db.flush()
        audit(db, actor, "expense", expense.id, "created", violation)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        constraint = getattr(getattr(exc.orig, "diag", None), "constraint_name", None)
        duplicate_constraints = {
            "uq_expense_invoice_key",
            "uq_expense_merchant_date_amount",
        }
        if constraint in duplicate_constraints or "UNIQUE constraint failed" in str(exc.orig):
            raise HTTPException(status.HTTP_409_CONFLICT, "Despesa duplicada") from exc
        raise
    db.refresh(expense)
    return expense


TRANSITIONS = {
    "submit": ({ExpenseStatus.draft, ExpenseStatus.rejected}, ExpenseStatus.submitted),
    "approve": ({ExpenseStatus.submitted}, ExpenseStatus.approved),
    "reject": ({ExpenseStatus.submitted}, ExpenseStatus.rejected),
    "reimburse": ({ExpenseStatus.approved}, ExpenseStatus.reimbursed),
}


def transition(
    db: Session, actor: User, expense: Expense, action: str, comment: str | None = None
) -> Expense:
    allowed, target = TRANSITIONS[action]
    if expense.status not in allowed:
        raise HTTPException(status.HTTP_409_CONFLICT, "Transição de status inválida")
    if action == "submit":
        # A rejected expense can be edited and resubmitted with a fresh approval chain.
        db.execute(delete(Approval).where(Approval.expense_id == expense.id))
        levels = 2 if expense.amount > 5000 else 1
        for level in range(1, levels + 1):
            db.add(
                Approval(
                    organization_id=actor.organization_id,
                    expense_id=expense.id,
                    level=level,
                )
            )
    elif action in {"approve", "reject"}:
        approval = db.scalar(
            select(Approval)
            .where(
                Approval.expense_id == expense.id,
                Approval.decision == ApprovalDecision.pending,
            )
            .order_by(Approval.level)
        )
        if not approval:
            raise HTTPException(status.HTTP_409_CONFLICT, "Aprovação pendente não encontrada")
        approval.approver_id = actor.id
        approval.decision = (
            ApprovalDecision.approved if action == "approve" else ApprovalDecision.rejected
        )
        approval.comment = comment
        approval.decided_at = datetime.now(UTC)
        if action == "approve" and db.scalar(
            select(Approval.id).where(
                Approval.expense_id == expense.id,
                Approval.decision == ApprovalDecision.pending,
                Approval.level > approval.level,
            )
        ):
            target = ExpenseStatus.submitted
    expense.status = target
    audit(db, actor, "expense", expense.id, action)
    db.commit()
    db.refresh(expense)
    return expense
