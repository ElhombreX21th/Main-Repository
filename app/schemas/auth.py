import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.entities import UserRole


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=160)
    organization_name: str = Field(min_length=2, max_length=160)
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    country_code: str = Field(default="BR", min_length=2, max_length=2)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    first_name: str | None = None
    role: UserRole | None = None


class UserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=160)
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    role: UserRole = UserRole.employee


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    full_name: str | None
    email: EmailStr
    role: UserRole
    is_active: bool
