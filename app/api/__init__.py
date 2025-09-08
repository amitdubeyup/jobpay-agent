"""
API module initialization with versioning support.
"""

from fastapi import APIRouter
from app.api.v1 import api_v1_router
from app.monitoring import health_checker, metrics

# Main API router
api_router = APIRouter()

# Include versioned API routers
api_router.include_router(api_v1_router, prefix="/v1")

# Health and metrics endpoints (version-agnostic)
@api_router.get("/health")
async def health_check():
    """Comprehensive health check endpoint."""
    return await health_checker.comprehensive_health_check()

@api_router.get("/health/simple")
async def simple_health_check():
    """Simple health check for load balancers."""
    return {"status": "healthy", "service": "jobpay-agent"}

@api_router.get("/metrics")
async def get_metrics():
    """Get application metrics."""
    return {
        "system": metrics.get_system_metrics(),
        "requests": metrics.get_request_metrics(),
        "endpoints": metrics.get_endpoint_metrics(),
        "errors": metrics.get_error_metrics()
    }

@api_router.get("/version")
async def get_version():
    """Get API version information."""
    return {
        "api_version": "1.0",
        "supported_versions": ["v1"],
        "current_version": "v1",
        "deprecation_notice": None
    }

__all__ = ["api_router"]
