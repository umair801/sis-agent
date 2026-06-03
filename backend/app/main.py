from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.api.v1.router import api_router
import app.models  # noqa: F401 — registers all models with Base.metadata


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(debug=settings.APP_DEBUG)
    logger.info("SIS API starting up", env=settings.APP_ENV)
    yield
    logger.info("SIS API shutting down")


app = FastAPI(
    title="SIS API",
    description="AI-powered Student Information System by Datawebify",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["System"])
async def root_health():
    return {"status": "ok", "service": "SIS API"}
