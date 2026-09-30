import time
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.core.database import engine, Base
from backend.app.core.logging import logger
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

# -------------------------------------------------------------
# Middleware: Audit Logging and Request Timing
# -------------------------------------------------------------
@app.middleware("http")
async def audit_logging_middleware(request: Request, call_next):
    start_time = time.time()
    client_ip = request.client.host if request.client else "unknown"
    
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000  # milliseconds
    logger.info(
        f"[HTTP] {request.method} {request.url.path} "
        f"status={response.status_code} "
        f"ip={client_ip} "
        f"latency={process_time:.2f}ms"
    )
    response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

# -------------------------------------------------------------
# Custom Exception Handlers for Clean API Error Responses
# -------------------------------------------------------------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        field = " -> ".join([str(loc) for loc in err.get("loc", []) if loc != "body"])
        errors.append({
            "field": field,
            "message": err.get("msg", "Validation error"),
            "type": err.get("type", "value_error")
        })
    logger.warning(f"[VALIDATION_ERROR] Path={request.url.path} Errors={errors}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error_type": "ValidationError",
            "message": "Input validation failed. Please check the submitted fields.",
            "details": errors
        }
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.warning(f"[HTTP_EXCEPTION] {request.method} {request.url.path} status={exc.status_code} detail={exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "status_code": exc.status_code,
            "detail": exc.detail
        },
        headers=exc.headers
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"[UNHANDLED_EXCEPTION] {request.method} {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "status_code": 500,
            "detail": "An internal server error occurred while processing the emergency request."
        }
    )

# -------------------------------------------------------------
# Routers
# -------------------------------------------------------------
from backend.app.routers.auth import router as auth_router
from backend.app.routers.alerts import router as alerts_router
from backend.app.routers.locations import router as locations_router
from backend.app.routers.escalation import router as escalation_router

app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(alerts_router, prefix=settings.API_V1_STR)
app.include_router(locations_router, prefix=settings.API_V1_STR)
app.include_router(escalation_router, prefix=settings.API_V1_STR)

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
