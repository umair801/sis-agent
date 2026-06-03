from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.db.database import get_db
from app.models.user import User, Role
from app.models.tenant import Tenant
from app.core.security import verify_password, hash_password, create_access_token, create_refresh_token, decode_token
from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest
from datetime import datetime, timezone

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    # Resolve tenant
    tenant_result = await db.execute(
        select(Tenant).where(Tenant.slug == payload.tenant_slug, Tenant.is_active == True)
    )
    tenant = tenant_result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Resolve user
    user_result = await db.execute(
        select(User).where(
            and_(User.email == payload.email, User.tenant_id == tenant.id, User.is_active == True)
        )
    )
    user = user_result.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Resolve role name
    role_result = await db.execute(select(Role).where(Role.id == user.role_id))
    role = role_result.scalar_one_or_none()
    role_name = role.name if role else "Unknown"

    # Update last login
    user.last_login = datetime.now(timezone.utc)
    await db.commit()

    token_data = {
        "sub": str(user.id),
        "tenant_id": str(tenant.id),
        "role": role_name,
    }

    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
        tenant_id=str(tenant.id),
        role=role_name,
        user_id=str(user.id),
        full_name=f"{user.first_name} {user.last_name}",
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    data = decode_token(payload.refresh_token)
    if not data or data.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    token_data = {
        "sub": data["sub"],
        "tenant_id": data["tenant_id"],
        "role": data["role"],
    }

    # Fetch user for full_name
    from uuid import UUID
    user_result = await db.execute(select(User).where(User.id == UUID(data["sub"])))
    user = user_result.scalar_one_or_none()
    full_name = f"{user.first_name} {user.last_name}" if user else ""

    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
        tenant_id=data["tenant_id"],
        role=data["role"],
        user_id=data["sub"],
        full_name=full_name,
    )
