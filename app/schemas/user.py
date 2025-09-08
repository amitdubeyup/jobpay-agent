from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.models.user import UserRole


class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    role: UserRole


class UserCreate(UserBase):
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None


class UserInDB(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class User(UserInDB):
    pass


class CandidateBase(BaseModel):
    location: Optional[str] = None
    skills: List[str] = []
    hobbies: List[str] = []
    experience_years: Optional[int] = None
    education: Optional[str] = None
    bio: Optional[str] = None
    preferences: Dict[str, Any] = {}


class CandidateCreate(CandidateBase):
    user: UserCreate


class CandidateUpdate(CandidateBase):
    pass


class CandidateInDB(CandidateBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class Candidate(CandidateInDB):
    user: User


class EmployerBase(BaseModel):
    company_name: str
    company_description: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    location: Optional[str] = None


class EmployerCreate(EmployerBase):
    user: UserCreate


class EmployerUpdate(EmployerBase):
    pass


class EmployerInDB(EmployerBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class Employer(EmployerInDB):
    user: User


# Auth schemas
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str
