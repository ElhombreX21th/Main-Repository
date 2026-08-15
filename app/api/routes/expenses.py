import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_user, require_roles
from app.core.config import settings
from app.db.session import get_db
from app.models.entities import Expense, User, UserRole
from app.parsers import parse_br_receipt
from app.schemas.expense import (
    DecisionRequest,
    ExpenseCreate,
    ExpenseRead,
    ParsedReceipt,
    ReceiptText,
)
from app.services.audit import audit
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
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Despesa não encontrada")
    return expense


@router.post("/{expense_id}/submit", response_model=ExpenseRead)
def submit(
    expense_id: uuid.UUID, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    expense = tenant_expense(expense_id, user, db)
    if expense.user_id != user.id and user.role != UserRole.admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Apenas o proprietário pode enviar")
    return transition(db, user, expense, "submit")


def workflow_route(action: str):
    def route(
        expense_id: uuid.UUID,
        payload: DecisionRequest | None = None,
        user: User = Depends(require_roles(UserRole.approver, UserRole.admin)),
        db: Session = Depends(get_db),
    ):
        return transition(
            db,
            user,
            tenant_expense(expense_id, user, db),
            action,
            payload.comment if payload else None,
        )

    return route


for action in ("approve", "reject", "reimburse"):
    router.add_api_route(
        f"/{{expense_id}}/{action}",
        workflow_route(action),
        methods=["POST"],
        response_model=ExpenseRead,
    )


@router.post("/{expense_id}/receipt", response_model=ExpenseRead)
def upload_receipt(
    expense_id: uuid.UUID,
    receipt: UploadFile = File(...),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    expense = tenant_expense(expense_id, user, db)
    if expense.user_id != user.id and user.role != UserRole.admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Apenas o proprietário pode anexar")
    if receipt.content_type not in {"image/jpeg", "image/png", "application/pdf", "text/plain"}:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Formato não suportado")
    content = receipt.file.read(5 * 1024 * 1024 + 1)
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Arquivo excede 5 MB")
    suffix = Path(receipt.filename or "receipt.bin").suffix.lower()
    directory = Path(settings.receipt_storage_path) / str(user.organization_id)
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / f"{expense.id}{suffix}"
    destination.write_bytes(content)
    expense.receipt_path = str(destination)
    audit(db, user, "expense", expense.id, "receipt_uploaded", receipt.content_type)
    db.commit()
    db.refresh(expense)
    return expense
