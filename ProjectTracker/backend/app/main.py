"""
ProjectTracker — FastAPI entry point.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base, SessionLocal
from .routers import auth, projects, reports
from . import crud
from .config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables and seed demo data on startup
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        crud.seed_demo_data(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "REST API for managing team projects and initiatives. "
        "Designed to run on-premise without SaaS dependencies."
    ),
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    redirect_slashes=False,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,     prefix="/api/auth",     tags=["Auth"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(reports.router,  prefix="/api/reports",  tags=["Reports"])


@app.get("/api/health", tags=["Health"])
def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}
