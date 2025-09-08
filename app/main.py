from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time
import logging

from app.core.config import settings
from app.api import api_router
from app.middleware import (
    RateLimitMiddleware, 
    RequestLoggingMiddleware, 
    ErrorHandlingMiddleware,
    MetricsMiddleware
)
from app.exceptions import JobPayException
from app.monitoring import metrics, health_checker
from app.docs import create_openapi_schema

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Create FastAPI app with enhanced metadata
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    contact={
        "name": "JobPay India",
        "url": "https://jobpay.in",
        "email": "support@jobpay.in"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    servers=[
        {
            "url": "/",
            "description": "Current environment"
        }
    ]
)

# Set custom OpenAPI schema
app.openapi = lambda: create_openapi_schema(app)

# Add custom middleware in order (last added = first executed)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware)

# Add CORS middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Response-Time", "X-Request-ID"]
    )

# Add trusted host middleware
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])


# Custom exception handlers for JobPay exceptions
@app.exception_handler(JobPayException)
async def jobpay_exception_handler(request: Request, exc: JobPayException):
    """Handle JobPay custom exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details,
            "path": str(request.url.path),
            "timestamp": time.time()
        }
    )


# Default exception handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": True,
            "error_code": "NOT_FOUND",
            "message": "Not found",
            "path": str(request.url.path),
            "timestamp": time.time()
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "Internal server error",
            "timestamp": time.time()
        }
    )


# Application event handlers
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    # Perform startup health checks
    health_status = await health_checker.comprehensive_health_check()
    if health_status["status"] == "unhealthy":
        logger.warning("Application started with unhealthy dependencies")
    else:
        logger.info("Application started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on application shutdown."""
    logger.info("Shutting down application")


# Include API routes
app.include_router(api_router, prefix="/api")


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": f"{settings.API_V1_STR}/docs",
        "health": f"{settings.API_V1_STR}/health",
        "metrics": f"{settings.API_V1_STR}/metrics",
        "api_version": "v1"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )
