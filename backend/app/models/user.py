from sqlalchemy import Column, String, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy import TIMESTAMP
from app.db.database import Base
import uuid


class Role(Base):
    __tablename__ = "sis_role"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id   = Column(UUID(as_uuid=True), ForeignKey("sis_tenant.id", ondelete="CASCADE"), nullable=False)
    name        = Column(Text, nullable=False)
    permissions = Column(String, default="{}")
    created_at  = Column(TIMESTAMP(timezone=True), server_default=func.now())


class User(Base):
    __tablename__ = "sis_user"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id       = Column(UUID(as_uuid=True), ForeignKey("sis_tenant.id", ondelete="CASCADE"), nullable=False)
    role_id         = Column(UUID(as_uuid=True), ForeignKey("sis_role.id"), nullable=False)
    email           = Column(Text, nullable=False)
    hashed_password = Column(Text, nullable=False)
    first_name      = Column(Text, nullable=False)
    last_name       = Column(Text, nullable=False)
    phone           = Column(Text)
    is_active       = Column(Boolean, default=True)
    last_login      = Column(TIMESTAMP(timezone=True))
    created_at      = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at      = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
