from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings
import re

# Convert postgresql:// to postgresql+asyncpg://
def make_async_url(url: str) -> str:
    return re.sub(r"^postgresql://", "postgresql+asyncpg://", url)

engine = create_async_engine(
    make_async_url(settings.DATABASE_URL),
    echo=settings.APP_DEBUG,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
