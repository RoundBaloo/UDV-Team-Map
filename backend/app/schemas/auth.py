from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    employee_id: int = Field(serialization_alias="employee_id", validation_alias="id")
    email: EmailStr
    first_name: str
    last_name: str
    title: str | None = None
    is_admin: bool
    is_blocked: bool
