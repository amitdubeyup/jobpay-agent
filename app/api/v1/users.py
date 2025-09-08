from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.security import get_current_active_user, require_role
from app.models.user import User, UserRole
from app.schemas.user import (
    Candidate, CandidateCreate, CandidateUpdate,
    Employer, EmployerCreate, EmployerUpdate
)
from app.schemas.job import JobMatch, PaginatedJobs
from app.services.user_service import CandidateService, EmployerService
from app.services.job_service import JobMatchService
from app.workers.notification_tasks import send_welcome_notification_task
from app.db.session import get_db

router = APIRouter()


@router.post("/candidates", response_model=Candidate, status_code=status.HTTP_201_CREATED)
async def create_candidate(
    candidate_data: CandidateCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new candidate."""
    candidate_service = CandidateService(db)
    
    # Check if email already exists
    from app.services.user_service import UserService
    user_service = UserService(db)
    existing_user = await user_service.get_by_email(candidate_data.user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    candidate = await candidate_service.create_candidate(candidate_data)
    
    # Queue welcome notification
    send_welcome_notification_task.delay(
        candidate.id, 
        candidate.user.full_name
    )
    
    return candidate


@router.get("/candidates/me", response_model=Candidate)
async def get_my_profile(
    current_user: User = Depends(require_role(UserRole.CANDIDATE)),
    db: AsyncSession = Depends(get_db)
):
    """Get current candidate's profile."""
    candidate_service = CandidateService(db)
    candidate = await candidate_service.get_by_user_id(current_user.id)
    
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate profile not found"
        )
    
    return candidate


@router.put("/candidates/me", response_model=Candidate)
async def update_my_profile(
    candidate_data: CandidateUpdate,
    current_user: User = Depends(require_role(UserRole.CANDIDATE)),
    db: AsyncSession = Depends(get_db)
):
    """Update current candidate's profile."""
    candidate_service = CandidateService(db)
    candidate = await candidate_service.get_by_user_id(current_user.id)
    
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate profile not found"
        )
    
    updated_candidate = await candidate_service.update_candidate(candidate.id, candidate_data)
    return updated_candidate


@router.get("/candidates/{candidate_id}", response_model=Candidate)
async def get_candidate(
    candidate_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get candidate by ID (employers only)."""
    if current_user.role != UserRole.EMPLOYER and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only employers can view candidate profiles"
        )
    
    candidate_service = CandidateService(db)
    candidate = await candidate_service.get_by_id(candidate_id)
    
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found"
        )
    
    return candidate


@router.get("/candidates/me/matches", response_model=List[JobMatch])
async def get_my_job_matches(
    current_user: User = Depends(require_role(UserRole.CANDIDATE)),
    db: AsyncSession = Depends(get_db)
):
    """Get job matches for current candidate."""
    candidate_service = CandidateService(db)
    candidate = await candidate_service.get_by_user_id(current_user.id)
    
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate profile not found"
        )
    
    job_match_service = JobMatchService(db)
    matches = await job_match_service.get_matches_for_candidate(candidate.id)
    
    return matches


@router.post("/employers", response_model=Employer, status_code=status.HTTP_201_CREATED)
async def create_employer(
    employer_data: EmployerCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new employer."""
    employer_service = EmployerService(db)
    
    # Check if email already exists
    from app.services.user_service import UserService
    user_service = UserService(db)
    existing_user = await user_service.get_by_email(employer_data.user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    employer = await employer_service.create_employer(employer_data)
    return employer


@router.get("/employers/me", response_model=Employer)
async def get_my_employer_profile(
    current_user: User = Depends(require_role(UserRole.EMPLOYER)),
    db: AsyncSession = Depends(get_db)
):
    """Get current employer's profile."""
    employer_service = EmployerService(db)
    employer = await employer_service.get_by_user_id(current_user.id)
    
    if not employer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employer profile not found"
        )
    
    return employer


@router.put("/employers/me", response_model=Employer)
async def update_my_employer_profile(
    employer_data: EmployerUpdate,
    current_user: User = Depends(require_role(UserRole.EMPLOYER)),
    db: AsyncSession = Depends(get_db)
):
    """Update current employer's profile."""
    employer_service = EmployerService(db)
    employer = await employer_service.get_by_user_id(current_user.id)
    
    if not employer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employer profile not found"
        )
    
    updated_employer = await employer_service.update_employer(employer.id, employer_data)
    return updated_employer
