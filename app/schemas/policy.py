import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PolicyCreate(BaseModel):
    category: str = Field(min_length=2, max_length=80)
    country_code: str = Field(default="BR", min_length=2, max_length=2)
    currency: str = Field(default="BRL", min_length=3, max_length=3)
    max_amount: Decimal = Field(gt=0, decimal_places=2)


class PolicyRead(PolicyCreate):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
