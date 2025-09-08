from pydantic import BaseModel, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.models.job import JobType, JobStatus


class JobBase(BaseModel):
    title: str
    description: str
    company: str
    location: Optional[str] = None
    required_skills: List[str] = []
    nice_to_have_skills: List[str] = []
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    currency: str = "USD"
    job_type: JobType = JobType.FULL_TIME
    remote_allowed: Optional[str] = None
    experience_min: Optional[int] = None
    experience_max: Optional[int] = None
    benefits: List[str] = []
    application_url: Optional[str] = None
    application_email: Optional[str] = None
    expires_at: Optional[datetime] = None
    
    @validator('salary_min', 'salary_max')
    def validate_salary(cls, v):
        if v is not None and v < 0:
            raise ValueError('Salary must be positive')
        return v
    
    @validator('experience_min', 'experience_max')
    def validate_experience(cls, v):
        if v is not None and v < 0:
            raise ValueError('Experience must be positive')
        return v


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    required_skills: Optional[List[str]] = None
    nice_to_have_skills: Optional[List[str]] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    currency: Optional[str] = None
    job_type: Optional[JobType] = None
    status: Optional[JobStatus] = None
    remote_allowed: Optional[str] = None
    experience_min: Optional[int] = None
    experience_max: Optional[int] = None
    benefits: Optional[List[str]] = None
    application_url: Optional[str] = None
    application_email: Optional[str] = None
    expires_at: Optional[datetime] = None


class JobInDB(JobBase):
    id: int
    employer_id: int
    status: JobStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class Job(JobInDB):
    pass


class JobWithMatches(Job):
    matches_count: int
    top_candidates: List[Dict[str, Any]] = []


class JobMatchBase(BaseModel):
    job_id: int
    candidate_id: int
    overall_score: float
    skills_score: Optional[float] = None
    location_score: Optional[float] = None
    experience_score: Optional[float] = None
    salary_score: Optional[float] = None
    matching_skills: List[str] = []
    missing_skills: List[str] = []
    match_reasons: Dict[str, Any] = {}


class JobMatchCreate(JobMatchBase):
    pass


class JobMatchInDB(JobMatchBase):
    id: int
    is_notified: bool
    notified_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class JobMatch(JobMatchInDB):
    pass


class JobMatchWithDetails(JobMatch):
    job: Job
    candidate: Dict[str, Any]  # Basic candidate info


class JobSearchFilters(BaseModel):
    title: Optional[str] = None
    location: Optional[str] = None
    skills: Optional[List[str]] = None
    job_type: Optional[JobType] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    experience_min: Optional[int] = None
    experience_max: Optional[int] = None
    remote_allowed: Optional[str] = None
    company: Optional[str] = None


class PaginatedJobs(BaseModel):
    items: List[Job]
    total: int
    page: int
    size: int
    pages: int
