from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    organization_name: str = Field(min_length=2, max_length=160)
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    country_code: str = Field(default="BR", min_length=2, max_length=2)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
