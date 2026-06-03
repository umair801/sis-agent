from sqlalchemy import Column, String, Boolean, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy import TIMESTAMP
from app.db.database import Base
import uuid


class Tenant(Base):
    __tablename__ = "sis_tenant"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name          = Column(Text, nullable=False)
    slug          = Column(Text, nullable=False, unique=True)
    domain        = Column(Text)
    logo_url      = Column(Text)
    primary_color = Column(Text, default="#1a56db")
    grading_scale = Column(JSON, default={"A": 90, "B": 80, "C": 70, "D": 60})
    timezone      = Column(Text, default="America/Los_Angeles")
    is_active     = Column(Boolean, default=True)
    created_at    = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at    = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
