from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from app.models.user import User, Candidate, Employer, UserRole
from app.schemas.user import UserCreate, UserUpdate, CandidateCreate, CandidateUpdate, EmployerCreate, EmployerUpdate
from app.core.security import get_password_hash, verify_password


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user."""
        hashed_password = get_password_hash(user_data.password)
        
        user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            phone=user_data.phone,
            role=user_data.role,
        )
        
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """Update user."""
        user = await self.get_by_id(user_id)
        if not user:
            return None
        
        update_data = user_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password."""
        user = await self.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            return None
        return user
    
    async def deactivate_user(self, user_id: int) -> bool:
        """Deactivate user."""
        user = await self.get_by_id(user_id)
        if not user:
            return False
        
        user.is_active = False
        await self.db.commit()
        return True


class CandidateService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, candidate_id: int) -> Optional[Candidate]:
        """Get candidate by ID with user info."""
        result = await self.db.execute(
            select(Candidate)
            .options(selectinload(Candidate.user))
            .where(Candidate.id == candidate_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_user_id(self, user_id: int) -> Optional[Candidate]:
        """Get candidate by user ID."""
        result = await self.db.execute(
            select(Candidate)
            .options(selectinload(Candidate.user))
            .where(Candidate.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def create_candidate(self, candidate_data: CandidateCreate) -> Candidate:
        """Create a new candidate with user."""
        user_service = UserService(self.db)
        user = await user_service.create_user(candidate_data.user)
        
        candidate = Candidate(
            user_id=user.id,
            location=candidate_data.location,
            skills=candidate_data.skills,
            hobbies=candidate_data.hobbies,
            experience_years=candidate_data.experience_years,
            education=candidate_data.education,
            bio=candidate_data.bio,
            preferences=candidate_data.preferences,
        )
        
        self.db.add(candidate)
        await self.db.commit()
        await self.db.refresh(candidate)
        
        # Load user relationship
        result = await self.db.execute(
            select(Candidate)
            .options(selectinload(Candidate.user))
            .where(Candidate.id == candidate.id)
        )
        return result.scalar_one()
    
    async def update_candidate(self, candidate_id: int, candidate_data: CandidateUpdate) -> Optional[Candidate]:
        """Update candidate."""
        candidate = await self.get_by_id(candidate_id)
        if not candidate:
            return None
        
        update_data = candidate_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(candidate, field, value)
        
        await self.db.commit()
        await self.db.refresh(candidate)
        return candidate
    
    async def search_candidates(
        self,
        skills: Optional[List[str]] = None,
        location: Optional[str] = None,
        experience_min: Optional[int] = None,
        experience_max: Optional[int] = None,
        limit: int = 50
    ) -> List[Candidate]:
        """Search candidates based on criteria."""
        query = select(Candidate).options(selectinload(Candidate.user))
        
        conditions = []
        
        if skills:
            # Use array overlap operator for skills matching
            conditions.append(Candidate.skills.op('&&')(skills))
        
        if location:
            conditions.append(Candidate.location.ilike(f"%{location}%"))
        
        if experience_min is not None:
            conditions.append(Candidate.experience_years >= experience_min)
        
        if experience_max is not None:
            conditions.append(Candidate.experience_years <= experience_max)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()


class EmployerService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, employer_id: int) -> Optional[Employer]:
        """Get employer by ID with user info."""
        result = await self.db.execute(
            select(Employer)
            .options(selectinload(Employer.user))
            .where(Employer.id == employer_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_user_id(self, user_id: int) -> Optional[Employer]:
        """Get employer by user ID."""
        result = await self.db.execute(
            select(Employer)
            .options(selectinload(Employer.user))
            .where(Employer.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def create_employer(self, employer_data: EmployerCreate) -> Employer:
        """Create a new employer with user."""
        user_service = UserService(self.db)
        user = await user_service.create_user(employer_data.user)
        
        employer = Employer(
            user_id=user.id,
            company_name=employer_data.company_name,
            company_description=employer_data.company_description,
            website=employer_data.website,
            industry=employer_data.industry,
            size=employer_data.size,
            location=employer_data.location,
        )
        
        self.db.add(employer)
        await self.db.commit()
        await self.db.refresh(employer)
        
        # Load user relationship
        result = await self.db.execute(
            select(Employer)
            .options(selectinload(Employer.user))
            .where(Employer.id == employer.id)
        )
        return result.scalar_one()
    
    async def update_employer(self, employer_id: int, employer_data: EmployerUpdate) -> Optional[Employer]:
        """Update employer."""
        employer = await self.get_by_id(employer_id)
        if not employer:
            return None
        
        update_data = employer_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(employer, field, value)
        
        await self.db.commit()
        await self.db.refresh(employer)
        return employer
