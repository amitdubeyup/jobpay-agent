from sqlalchemy import Column, Integer, String, DateTime, Text, ARRAY, JSON, ForeignKey, Float, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects import postgresql, sqlite
from app.db.session import Base
import enum


class JobType(str, enum.Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    FREELANCE = "freelance"
    INTERNSHIP = "internship"


class JobStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"
    DRAFT = "draft"


class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=False)
    company = Column(String, nullable=False, index=True)
    location = Column(String, nullable=True, index=True)
    required_skills = Column(JSON().with_variant(postgresql.ARRAY(String), 'postgresql'), nullable=False)
    nice_to_have_skills = Column(JSON().with_variant(postgresql.ARRAY(String), 'postgresql'), nullable=True)
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    currency = Column(String, default="USD")
    job_type = Column(SQLEnum(JobType), nullable=False, default=JobType.FULL_TIME)
    status = Column(SQLEnum(JobStatus), nullable=False, default=JobStatus.ACTIVE)
    remote_allowed = Column(String, nullable=True)  # remote, hybrid, onsite
    experience_min = Column(Integer, nullable=True)
    experience_max = Column(Integer, nullable=True)
    benefits = Column(JSON().with_variant(postgresql.ARRAY(String), 'postgresql'), nullable=True)
    application_url = Column(String, nullable=True)
    application_email = Column(String, nullable=True)
    
    # Foreign Keys
    employer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    employer = relationship("User", back_populates="jobs")
    matches = relationship("JobMatch", back_populates="job")


class JobMatch(Base):
    __tablename__ = "job_matches"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    
    # Matching scores
    overall_score = Column(Float, nullable=False)
    skills_score = Column(Float, nullable=True)
    location_score = Column(Float, nullable=True)
    experience_score = Column(Float, nullable=True)
    salary_score = Column(Float, nullable=True)
    
    # Matching details
    matching_skills = Column(JSON().with_variant(postgresql.ARRAY(String), 'postgresql'), nullable=True)
    missing_skills = Column(JSON().with_variant(postgresql.ARRAY(String), 'postgresql'), nullable=True)
    match_reasons = Column(JSON, nullable=True)
    
    # Status tracking
    is_notified = Column(String, default=False)
    notified_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    job = relationship("Job", back_populates="matches")
    candidate = relationship("Candidate", back_populates="matches")
