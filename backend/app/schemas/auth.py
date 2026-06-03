from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    tenant_slug: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    tenant_id: str
    role: str
    user_id: str
    full_name: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPayload(BaseModel):
    sub: str
    tenant_id: str
    role: str
    type: str
    exp: Optional[int] = None
