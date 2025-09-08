from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.core.security import get_current_active_user, require_role
from app.models.user import User, UserRole
from app.schemas.job import (
    Job, JobCreate, JobUpdate, JobSearchFilters, 
    PaginatedJobs, JobMatch, JobWithMatches
)
from app.services.job_service import JobService, JobMatchService
from app.services.user_service import EmployerService
from app.workers.matching_tasks import process_job_matching
from app.workers.notification_tasks import send_job_posted_notification_task
from app.db.session import get_db

router = APIRouter()


@router.post("/jobs", response_model=Job, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: JobCreate,
    current_user: User = Depends(require_role(UserRole.EMPLOYER)),
    db: AsyncSession = Depends(get_db)
):
    """Create a new job posting."""
    job_service = JobService(db)
    employer_service = EmployerService(db)
    
    # Get employer profile
    employer = await employer_service.get_by_user_id(current_user.id)
    if not employer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employer profile not found"
        )
    
    # Create job
    job = await job_service.create_job(job_data, current_user.id)
    
    # Queue matching task
    process_job_matching.delay(job.id)
    
    # Queue job posted notification
    send_job_posted_notification_task.delay(
        current_user.id,
        current_user.full_name,
        job.title
    )
    
    return job


@router.get("/jobs", response_model=List[Job])
async def search_jobs(
    title: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    skills: Optional[str] = Query(None),  # Comma-separated skills
    job_type: Optional[str] = Query(None),
    salary_min: Optional[float] = Query(None),
    salary_max: Optional[float] = Query(None),
    experience_min: Optional[int] = Query(None),
    experience_max: Optional[int] = Query(None),
    remote_allowed: Optional[str] = Query(None),
    company: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Search jobs with filters."""
    job_service = JobService(db)
    
    # Parse skills from comma-separated string
    skills_list = None
    if skills:
        skills_list = [skill.strip() for skill in skills.split(",")]
    
    # Create filters
    filters = JobSearchFilters(
        title=title,
        location=location,
        skills=skills_list,
        job_type=job_type,
        salary_min=salary_min,
        salary_max=salary_max,
        experience_min=experience_min,
        experience_max=experience_max,
        remote_allowed=remote_allowed,
        company=company
    )
    
    # Calculate offset
    offset = (page - 1) * size
    
    # Search jobs
    jobs = await job_service.search_jobs(filters, limit=size, offset=offset)
    
    return jobs


@router.get("/jobs/{job_id}", response_model=Job)
async def get_job(
    job_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get job by ID."""
    job_service = JobService(db)
    job = await job_service.get_by_id(job_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    return job


@router.put("/jobs/{job_id}", response_model=Job)
async def update_job(
    job_id: int,
    job_data: JobUpdate,
    current_user: User = Depends(require_role(UserRole.EMPLOYER)),
    db: AsyncSession = Depends(get_db)
):
    """Update job posting."""
    job_service = JobService(db)
    
    # Get job and verify ownership
    job = await job_service.get_by_id(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    if job.employer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this job"
        )
    
    # Update job
    updated_job = await job_service.update_job(job_id, job_data)
    
    # If significant changes, trigger re-matching
    significant_fields = {'required_skills', 'location', 'salary_min', 'salary_max', 'experience_min', 'experience_max'}
    updated_fields = set(job_data.dict(exclude_unset=True).keys())
    
    if significant_fields & updated_fields:
        process_job_matching.delay(job.id)
    
    return updated_job


@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: int,
    current_user: User = Depends(require_role(UserRole.EMPLOYER)),
    db: AsyncSession = Depends(get_db)
):
    """Delete (close) job posting."""
    job_service = JobService(db)
    
    # Get job and verify ownership
    job = await job_service.get_by_id(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    if job.employer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this job"
        )
    
    # Delete (close) job
    success = await job_service.delete_job(job_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete job"
        )


@router.get("/jobs/{job_id}/matches", response_model=List[JobMatch])
async def get_job_matches(
    job_id: int,
    current_user: User = Depends(require_role(UserRole.EMPLOYER)),
    db: AsyncSession = Depends(get_db)
):
    """Get candidate matches for a job."""
    job_service = JobService(db)
    job_match_service = JobMatchService(db)
    
    # Get job and verify ownership
    job = await job_service.get_by_id(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    if job.employer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view matches for this job"
        )
    
    # Get matches
    matches = await job_match_service.get_matches_for_job(job_id)
    
    return matches


@router.get("/my-jobs", response_model=List[Job])
async def get_my_jobs(
    current_user: User = Depends(require_role(UserRole.EMPLOYER)),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get jobs posted by current employer."""
    job_service = JobService(db)
    
    offset = (page - 1) * size
    jobs = await job_service.get_jobs_by_employer(
        current_user.id, 
        limit=size, 
        offset=offset
    )
    
    return jobs


@router.post("/jobs/{job_id}/reprocess-matching")
async def reprocess_job_matching(
    job_id: int,
    current_user: User = Depends(require_role(UserRole.EMPLOYER)),
    db: AsyncSession = Depends(get_db)
):
    """Manually trigger job matching for a job."""
    job_service = JobService(db)
    
    # Get job and verify ownership
    job = await job_service.get_by_id(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    if job.employer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to reprocess matching for this job"
        )
    
    # Queue matching task
    task = process_job_matching.delay(job_id)
    
    return {
        "message": "Job matching queued for reprocessing",
        "task_id": task.id
    }
