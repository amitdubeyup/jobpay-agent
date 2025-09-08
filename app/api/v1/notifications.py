from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.security import get_current_active_user, require_role
from app.models.user import User, UserRole
from app.schemas.notification import (
    NotificationPreference, NotificationPreferenceUpdate,
    NotificationLog, NotificationRequest
)
from app.services.notification_service import NotificationPreferenceService, NotificationLogService
from app.services.user_service import CandidateService
from app.workers.notification_tasks import send_notification_task
from app.db.session import get_db

router = APIRouter()


@router.get("/preferences", response_model=NotificationPreference)
async def get_notification_preferences(
    current_user: User = Depends(require_role(UserRole.CANDIDATE)),
    db: AsyncSession = Depends(get_db)
):
    """Get notification preferences for current candidate."""
    candidate_service = CandidateService(db)
    notification_service = NotificationPreferenceService(db)
    
    # Get candidate
    candidate = await candidate_service.get_by_user_id(current_user.id)
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate profile not found"
        )
    
    # Get preferences
    preferences = await notification_service.get_by_candidate_id(candidate.id)
    if not preferences:
        # Create default preferences
        from app.schemas.notification import NotificationPreferenceCreate
        default_prefs = NotificationPreferenceCreate(candidate_id=candidate.id)
        preferences = await notification_service.create_preferences(default_prefs)
    
    return preferences


@router.put("/preferences", response_model=NotificationPreference)
async def update_notification_preferences(
    preferences_data: NotificationPreferenceUpdate,
    current_user: User = Depends(require_role(UserRole.CANDIDATE)),
    db: AsyncSession = Depends(get_db)
):
    """Update notification preferences for current candidate."""
    candidate_service = CandidateService(db)
    notification_service = NotificationPreferenceService(db)
    
    # Get candidate
    candidate = await candidate_service.get_by_user_id(current_user.id)
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate profile not found"
        )
    
    # Update preferences
    preferences = await notification_service.update_preferences(candidate.id, preferences_data)
    if not preferences:
        # Create if doesn't exist
        from app.schemas.notification import NotificationPreferenceCreate
        create_data = NotificationPreferenceCreate(
            candidate_id=candidate.id,
            **preferences_data.dict(exclude_unset=True)
        )
        preferences = await notification_service.create_preferences(create_data)
    
    return preferences


@router.get("/logs", response_model=List[NotificationLog])
async def get_notification_logs(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get notification logs for current user."""
    notification_log_service = NotificationLogService(db)
    
    # Determine recipient type based on user role
    if current_user.role == UserRole.CANDIDATE:
        candidate_service = CandidateService(db)
        candidate = await candidate_service.get_by_user_id(current_user.id)
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate profile not found"
            )
        recipient_id = candidate.id
        recipient_type = "candidate"
    else:
        recipient_id = current_user.id
        recipient_type = "user"
    
    logs = await notification_log_service.get_logs_by_recipient(
        recipient_id=recipient_id,
        recipient_type=recipient_type,
        limit=50
    )
    
    return logs


@router.post("/send", status_code=status.HTTP_202_ACCEPTED)
async def send_notification(
    notification_request: NotificationRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    """Send notification (admin only)."""
    
    # Convert notification request to task format
    notification_data = {
        'recipient_id': notification_request.recipient_id,
        'recipient_type': notification_request.recipient_type,
        'template_name': notification_request.template_name,
        'channels': [ch.value for ch in notification_request.channels],
        'context_data': notification_request.context_data or {},
        'priority': notification_request.priority
    }
    
    # Queue notification task
    task = send_notification_task.delay(notification_data)
    
    return {
        "message": "Notification queued for sending",
        "task_id": task.id
    }


@router.get("/test", status_code=status.HTTP_202_ACCEPTED)
async def test_notification(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Send test notification to current user."""
    
    # Determine recipient details
    if current_user.role == UserRole.CANDIDATE:
        candidate_service = CandidateService(db)
        candidate = await candidate_service.get_by_user_id(current_user.id)
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate profile not found"
            )
        recipient_id = candidate.id
        recipient_type = "candidate"
        template_name = "welcome_candidate"
    else:
        recipient_id = current_user.id
        recipient_type = "employer"
        template_name = "job_posted"
    
    # Prepare test notification data
    notification_data = {
        'recipient_id': recipient_id,
        'recipient_type': recipient_type,
        'template_name': template_name,
        'channels': ['email'],
        'context_data': {
            'candidate_name': current_user.full_name,
            'employer_name': current_user.full_name,
            'job_title': 'Test Job Posting',
            'subject': 'Test Notification from JobPay'
        },
        'priority': 'normal'
    }
    
    # Queue test notification
    task = send_notification_task.delay(notification_data)
    
    return {
        "message": "Test notification queued",
        "task_id": task.id
    }
