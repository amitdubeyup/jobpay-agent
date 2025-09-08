from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import selectinload
from app.models.job import Job, JobMatch, JobStatus
from app.models.user import Candidate
from app.schemas.job import JobCreate, JobUpdate, JobSearchFilters
from app.schemas.job import JobMatchCreate


class JobService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, job_id: int) -> Optional[Job]:
        """Get job by ID."""
        result = await self.db.execute(
            select(Job).where(Job.id == job_id)
        )
        return result.scalar_one_or_none()
    
    async def create_job(self, job_data: JobCreate, employer_id: int) -> Job:
        """Create a new job."""
        job = Job(
            **job_data.dict(),
            employer_id=employer_id
        )
        
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)
        return job
    
    async def update_job(self, job_id: int, job_data: JobUpdate) -> Optional[Job]:
        """Update job."""
        job = await self.get_by_id(job_id)
        if not job:
            return None
        
        update_data = job_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(job, field, value)
        
        await self.db.commit()
        await self.db.refresh(job)
        return job
    
    async def get_jobs_by_employer(
        self,
        employer_id: int,
        status: Optional[JobStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Job]:
        """Get jobs by employer."""
        query = select(Job).where(Job.employer_id == employer_id)
        
        if status:
            query = query.where(Job.status == status)
        
        query = query.order_by(desc(Job.created_at)).limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def search_jobs(
        self,
        filters: JobSearchFilters,
        limit: int = 50,
        offset: int = 0
    ) -> List[Job]:
        """Search jobs with filters."""
        query = select(Job).where(Job.status == JobStatus.ACTIVE)
        
        conditions = []
        
        if filters.title:
            conditions.append(Job.title.ilike(f"%{filters.title}%"))
        
        if filters.location:
            conditions.append(Job.location.ilike(f"%{filters.location}%"))
        
        if filters.skills:
            # Use array overlap operator for skills matching
            conditions.append(Job.required_skills.op('&&')(filters.skills))
        
        if filters.job_type:
            conditions.append(Job.job_type == filters.job_type)
        
        if filters.salary_min is not None:
            conditions.append(
                or_(
                    Job.salary_min >= filters.salary_min,
                    Job.salary_max >= filters.salary_min
                )
            )
        
        if filters.salary_max is not None:
            conditions.append(
                or_(
                    Job.salary_min <= filters.salary_max,
                    Job.salary_max <= filters.salary_max
                )
            )
        
        if filters.experience_min is not None:
            conditions.append(
                or_(
                    Job.experience_min >= filters.experience_min,
                    Job.experience_min.is_(None)
                )
            )
        
        if filters.experience_max is not None:
            conditions.append(
                or_(
                    Job.experience_max <= filters.experience_max,
                    Job.experience_max.is_(None)
                )
            )
        
        if filters.remote_allowed:
            conditions.append(Job.remote_allowed == filters.remote_allowed)
        
        if filters.company:
            conditions.append(Job.company.ilike(f"%{filters.company}%"))
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(desc(Job.created_at)).limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def count_jobs(self, filters: Optional[JobSearchFilters] = None) -> int:
        """Count total jobs matching filters."""
        query = select(func.count(Job.id)).where(Job.status == JobStatus.ACTIVE)
        
        if filters:
            conditions = []
            # Apply same filters as search_jobs
            if filters.title:
                conditions.append(Job.title.ilike(f"%{filters.title}%"))
            
            if filters.location:
                conditions.append(Job.location.ilike(f"%{filters.location}%"))
            
            if filters.skills:
                conditions.append(Job.required_skills.op('&&')(filters.skills))
            
            # Add other filter conditions...
            
            if conditions:
                query = query.where(and_(*conditions))
        
        result = await self.db.execute(query)
        return result.scalar()
    
    async def delete_job(self, job_id: int) -> bool:
        """Soft delete job by setting status to CLOSED."""
        job = await self.get_by_id(job_id)
        if not job:
            return False
        
        job.status = JobStatus.CLOSED
        await self.db.commit()
        return True


class JobMatchService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_match(self, match_data: JobMatchCreate) -> JobMatch:
        """Create a job match."""
        match = JobMatch(**match_data.dict())
        
        self.db.add(match)
        await self.db.commit()
        await self.db.refresh(match)
        return match
    
    async def get_matches_for_job(self, job_id: int, limit: int = 50) -> List[JobMatch]:
        """Get all matches for a job."""
        result = await self.db.execute(
            select(JobMatch)
            .options(selectinload(JobMatch.candidate))
            .where(JobMatch.job_id == job_id)
            .order_by(desc(JobMatch.overall_score))
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_matches_for_candidate(self, candidate_id: int, limit: int = 50) -> List[JobMatch]:
        """Get all matches for a candidate."""
        result = await self.db.execute(
            select(JobMatch)
            .options(selectinload(JobMatch.job))
            .where(JobMatch.candidate_id == candidate_id)
            .order_by(desc(JobMatch.overall_score))
            .limit(limit)
        )
        return result.scalars().all()
    
    async def mark_as_notified(self, match_id: int) -> bool:
        """Mark a match as notified."""
        result = await self.db.execute(
            select(JobMatch).where(JobMatch.id == match_id)
        )
        match = result.scalar_one_or_none()
        
        if not match:
            return False
        
        match.is_notified = True
        match.notified_at = func.now()
        await self.db.commit()
        return True
    
    async def get_unnotified_matches(self, limit: int = 100) -> List[JobMatch]:
        """Get matches that haven't been notified yet."""
        result = await self.db.execute(
            select(JobMatch)
            .options(selectinload(JobMatch.job), selectinload(JobMatch.candidate))
            .where(JobMatch.is_notified == False)
            .order_by(desc(JobMatch.overall_score))
            .limit(limit)
        )
        return result.scalars().all()
    
    async def bulk_create_matches(self, matches: List[JobMatchCreate]) -> List[JobMatch]:
        """Bulk create job matches."""
        match_objects = [JobMatch(**match.dict()) for match in matches]
        
        self.db.add_all(match_objects)
        await self.db.commit()
        
        # Refresh all objects
        for match in match_objects:
            await self.db.refresh(match)
        
        return match_objects
