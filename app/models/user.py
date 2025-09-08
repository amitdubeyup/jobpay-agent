from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ARRAY, JSON, Enum as SQLEnum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects import postgresql, sqlite
from app.db.session import Base
import enum


class UserRole(str, enum.Enum):
    CANDIDATE = "candidate"
    EMPLOYER = "employer"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.CANDIDATE)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    candidate_profile = relationship("Candidate", back_populates="user", uselist=False)
    employer_profile = relationship("Employer", back_populates="user", uselist=False)
    jobs = relationship("Job", back_populates="employer")


class Candidate(Base):
    __tablename__ = "candidates"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    location = Column(String, nullable=True)
    skills = Column(JSON().with_variant(postgresql.ARRAY(String), 'postgresql'), nullable=True)
    hobbies = Column(JSON().with_variant(postgresql.ARRAY(String), 'postgresql'), nullable=True)
    experience_years = Column(Integer, nullable=True)
    education = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    preferences = Column(JSON, nullable=True, default={})  # job_type, salary_range, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="candidate_profile")
    matches = relationship("JobMatch", back_populates="candidate")
    notification_preferences = relationship("NotificationPreference", back_populates="candidate")


class Employer(Base):
    __tablename__ = "employers"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    company_name = Column(String, nullable=False)
    company_description = Column(Text, nullable=True)
    website = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    size = Column(String, nullable=True)  # startup, small, medium, large, enterprise
    location = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="employer_profile")
