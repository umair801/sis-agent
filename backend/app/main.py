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
    title="SIS API — Westlake Unified School District",
    description=(
        "AI-powered Student Information System built by Datawebify. "
        "Multi-tenant SaaS platform with LangGraph orchestration, "
        "Claude AI integration, and RAG pipeline over district documents."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

ALLOWED_ORIGINS = [
    "https://sis.datawebify.com",
    "https://sis-api.datawebify.com",
    "http://localhost:5173",
    "http://localhost:80",
    "http://localhost",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.up\.railway\.app|https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["System"])
async def root():
    return {
        "service":  "SIS API",
        "version":  "1.0.0",
        "docs":     "/docs",
        "health":   "/api/v1/health",
        "built_by": "Datawebify",
        "website":  "https://datawebify.com",
    }
