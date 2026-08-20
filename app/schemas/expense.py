import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.entities import ExpenseStatus


class ExpenseCreate(BaseModel):
    category: str = Field(min_length=2, max_length=80)
    amount: Decimal = Field(gt=0, decimal_places=2)
    currency: str = Field(default="BRL", min_length=3, max_length=3)
    expense_date: date
    merchant_tax_id: str | None = None
    merchant_city: str | None = Field(default=None, max_length=120)
    merchant_state: str | None = Field(default=None, min_length=2, max_length=2)
    invoice_key: str | None = None
    country_code: str = Field(default="BR", min_length=2, max_length=2)
    description: str | None = Field(default=None, max_length=2000)


class ExpenseRead(ExpenseCreate):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    user_id: uuid.UUID
    status: ExpenseStatus
    policy_violation: str | None
    created_at: datetime


class ReceiptText(BaseModel):
    text: str = Field(min_length=1)


class ParsedReceipt(BaseModel):
    merchant_tax_id: str | None
    merchant_city: str | None
    merchant_state: str | None
    invoice_key: str | None
    expense_date: date | None
    amount: Decimal | None
