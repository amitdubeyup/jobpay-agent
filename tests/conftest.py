import pytest
import asyncio
import os
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import get_db, Base
from app.core.config import settings

# Test database URL (using SQLite for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Set test environment variables
os.environ.update({
    "DATABASE_URL": TEST_DATABASE_URL,
    "DATABASE_URL_SYNC": "sqlite:///./test.db", 
    "REDIS_URL": "redis://localhost:6379/0",
    "CELERY_BROKER_URL": "redis://localhost:6379/1",
    "CELERY_RESULT_BACKEND": "redis://localhost:6379/2",
    "SECRET_KEY": "test-secret-key",
    "OPENAI_API_KEY": "test-openai-key",
    "SMTP_HOST": "test-smtp",
    "SMTP_USER": "test@example.com",
    "SMTP_PASSWORD": "test-password",
    "TWILIO_ACCOUNT_SID": "test-twilio-sid",
    "TWILIO_AUTH_TOKEN": "test-twilio-token",
    "FIREBASE_PROJECT_ID": "test-firebase-project",
    "ENVIRONMENT": "test"
})

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
def client():
    """
    Create a test client with a fresh database for each test
    """
    async def create_tables():
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def drop_tables():
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    # Create tables
    asyncio.run(create_tables())
    
    # Override the database dependency
    app.dependency_overrides[get_db] = get_test_db
    
    # Mock all external dependencies
    patches = [
        patch('app.workers.notification_tasks.send_welcome_notification_task.delay'),
        patch('app.workers.notification_tasks.send_notification_task.delay'),
        patch('app.workers.notification_tasks.send_job_posted_notification_task.delay'),
        patch('app.workers.matching_tasks.process_job_matching.delay'),
        patch('redis.Redis'),
        patch('openai.ChatCompletion.create'),
        patch('openai.Embedding.create'),
        patch('smtplib.SMTP'),
        patch('twilio.rest.Client'),
        patch('firebase_admin.messaging.send'),
        patch('app.notifications.email_provider.EmailProvider.send'),
        patch('app.notifications.sms_provider.SMSProvider.send'),
        patch('app.notifications.push_provider.PushNotificationProvider.send'),
        patch('app.services.ai_matching_service.AIMatchingService.find_matching_candidates'),
    ]
    
    # Start all patches
    mocks = [p.start() for p in patches]
    
    try:
        # Configure Celery task mocks
        mocks[0].return_value = None  # send_welcome_notification_task
        mocks[1].return_value = None  # send_notification_task
        mocks[2].return_value = None  # send_job_posted_notification_task
        mocks[3].return_value = None  # process_job_matching
        
        # Configure Redis mock
        redis_instance = MagicMock()
        mocks[4].return_value = redis_instance
        redis_instance.ping.return_value = True
        redis_instance.set.return_value = True
        redis_instance.get.return_value = None
        
        # Configure OpenAI mocks
        mocks[5].return_value = MagicMock(choices=[
            MagicMock(message=MagicMock(content="Mocked AI response"))
        ])
        mocks[6].return_value = MagicMock(data=[
            MagicMock(embedding=[0.1] * 1536)
        ])
        
        # Configure external service mocks
        smtp_instance = MagicMock()
        mocks[7].return_value = smtp_instance
        smtp_instance.starttls.return_value = None
        smtp_instance.login.return_value = None
        smtp_instance.send_message.return_value = {}
        
        twilio_instance = MagicMock()
        mocks[8].return_value = twilio_instance
        twilio_instance.messages.create.return_value = MagicMock(sid="test_message_sid")
        
        mocks[9].return_value = "test_firebase_response"  # firebase send
        
        # Configure notification provider mocks
        mocks[10].return_value = AsyncMock(return_value={"success": True, "message_id": "test123"})  # email
        mocks[11].return_value = AsyncMock(return_value={"success": True, "message_id": "sms123"})  # sms
        mocks[12].return_value = AsyncMock(return_value={"success": True, "message_id": "push123"})  # push
        
        # Configure AI matching service mock
        mocks[13].return_value = AsyncMock(return_value=[])  # ai matching
        
        with TestClient(app) as test_client:
            yield test_client
            
    finally:
        # Stop all patches
        for p in patches:
            p.stop()
        
        # Clean up
        app.dependency_overrides.clear()
        asyncio.run(drop_tables())


@pytest.fixture
def test_candidate_data():
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
def test_employer_data():
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
def test_job_data():
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
