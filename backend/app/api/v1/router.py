from fastapi import APIRouter
from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.ai import router as ai_router
from app.api.v1.routes.rag import router as rag_router
from app.api.v1.routes.students import router as students_router
from app.api.v1.routes.attendance import router as attendance_router
from app.api.v1.routes.scheduling import router as scheduling_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(ai_router)
api_router.include_router(rag_router)
api_router.include_router(students_router)
api_router.include_router(attendance_router)
api_router.include_router(scheduling_router)