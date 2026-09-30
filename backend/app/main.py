from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.core.database import engine, Base
# Import all models so SQLAlchemy metadata is aware of them
import backend.app.models

# Initialize tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend API and Database Services for Campus Emergency Assistance App (P1 Role). Provides roll-number authentication, structured indoor location directory, instantaneous emergency dispatching, alert queue management, and human-in-the-loop escalation logic.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/openapi.json"
)

# Enable CORS for frontends (P2 Student App & P4 Admin Dashboard)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from backend.app.routers.auth import router as auth_router
app.include_router(auth_router, prefix=settings.API_V1_STR)

@app.get("/", tags=["General"])
def root():
    return {
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "documentation": "/docs",
        "role": "P1 - Backend & Data"
    }

@app.get("/health", tags=["General"])
def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "api_version": settings.VERSION
    }
