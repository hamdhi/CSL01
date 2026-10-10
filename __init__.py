from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.core.csrf import TrustedOriginMiddleware
from src.routes.admin_route import router as admin_router
from src.routes.auth_route import router as auth_router
from src.routes.ministry_route import router as ministry_router
from src.routes.role_route import router as role_router
from src.routes.student_route import router as student_router
from src.routes.teacher_route import router as teacher_router
from src.routes.zonal_officer_route import router as zonal_officer_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Seed the database on startup (dev only).

    The seed lives in ``seed.py`` at the project root and is intentionally kept
    out of the Alembic migrations. To disable seeding in production, simply
    delete ``seed.py`` -- this import fails cleanly and seeding is skipped.
    """
    try:
        from seed import run_seed

        run_seed()
    except ImportError:
        pass
    yield


app = FastAPI(
    title="API",
    description="Admin API for the Student Management System",
    version="1.0.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
app.add_middleware(
    TrustedOriginMiddleware,
    allowed_origins=settings.allowed_origins,
)

app.include_router(admin_router)
app.include_router(auth_router)
app.include_router(student_router)
app.include_router(teacher_router)
app.include_router(zonal_officer_router)
app.include_router(ministry_router)
app.include_router(role_router)



@app.get("/",tags=["Health"])
async def root():
    return {"message": "Healthy API"}
