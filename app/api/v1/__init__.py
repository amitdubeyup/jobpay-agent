from fastapi import APIRouter
from app.api import auth, users, jobs, notifications

# Create v1 API router
api_v1_router = APIRouter()

# Include all route modules
api_v1_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(users.router, prefix="/users", tags=["Users"])
api_v1_router.include_router(jobs.router, tags=["Jobs"])
api_v1_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
