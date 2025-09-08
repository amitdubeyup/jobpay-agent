import pytest
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import get_db, Base
from app.core.config import settings

# Test database URL (using SQLite for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_test_db():
    """Override database dependency for tests."""
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session():
    """Create a fresh database session for each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database override."""
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
async def test_candidate_data():
    """Sample candidate data for testing."""
    return {
        "user": {
            "email": "candidate@example.com",
            "password": "testpassword123",
            "full_name": "John Doe",
            "phone": "+1234567890",
            "role": "candidate"
        },
        "location": "San Francisco, CA",
        "skills": ["Python", "FastAPI", "PostgreSQL"],
        "hobbies": ["reading", "coding"],
        "experience_years": 5,
        "education": "Computer Science Degree",
        "bio": "Experienced software developer",
        "preferences": {
            "salary_min": 100000,
            "salary_max": 150000,
            "job_type": "full_time"
        }
    }


@pytest.fixture
async def test_employer_data():
    """Sample employer data for testing."""
    return {
        "user": {
            "email": "employer@example.com",
            "password": "testpassword123",
            "full_name": "Jane Smith",
            "phone": "+1234567891",
            "role": "employer"
        },
        "company_name": "TechCorp",
        "company_description": "Leading technology company",
        "website": "https://techcorp.com",
        "industry": "Technology",
        "size": "medium",
        "location": "San Francisco, CA"
    }


@pytest.fixture
async def test_job_data():
    """Sample job data for testing."""
    return {
        "title": "Senior Python Developer",
        "description": "We are looking for an experienced Python developer...",
        "company": "TechCorp",
        "location": "San Francisco, CA",
        "required_skills": ["Python", "FastAPI", "PostgreSQL"],
        "nice_to_have_skills": ["Docker", "AWS"],
        "salary_min": 120000,
        "salary_max": 160000,
        "currency": "USD",
        "job_type": "full_time",
        "remote_allowed": "hybrid",
        "experience_min": 3,
        "experience_max": 7,
        "benefits": ["health_insurance", "401k"],
        "application_email": "jobs@techcorp.com"
    }
