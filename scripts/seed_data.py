#!/usr/bin/env python3
"""
Seed script to populate the database with sample data for development and testing.
"""

import asyncio
import sys
import os

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.db.session import AsyncSessionLocal
from app.services.user_service import CandidateService, EmployerService
from app.services.job_service import JobService
from app.schemas.user import CandidateCreate, EmployerCreate, UserCreate
from app.schemas.job import JobCreate
from app.models.user import UserRole
from app.models.job import JobType


async def create_sample_candidates():
    """Create sample candidates."""
    async with AsyncSessionLocal() as db:
        candidate_service = CandidateService(db)
        
        candidates_data = [
            {
                "user": {
                    "email": "alice.developer@example.com",
                    "password": "password123",
                    "full_name": "Alice Johnson",
                    "phone": "+1-555-0101",
                    "role": UserRole.CANDIDATE
                },
                "location": "San Francisco, CA",
                "skills": ["Python", "FastAPI", "PostgreSQL", "React", "Docker"],
                "hobbies": ["hiking", "photography", "reading"],
                "experience_years": 5,
                "education": "Computer Science, UC Berkeley",
                "bio": "Passionate full-stack developer with 5 years of experience building scalable web applications.",
                "preferences": {
                    "salary_min": 120000,
                    "salary_max": 160000,
                    "job_type": "full_time",
                    "remote_preference": "hybrid"
                }
            },
            {
                "user": {
                    "email": "bob.engineer@example.com",
                    "password": "password123",
                    "full_name": "Bob Smith",
                    "phone": "+1-555-0102",
                    "role": UserRole.CANDIDATE
                },
                "location": "New York, NY",
                "skills": ["JavaScript", "Node.js", "MongoDB", "AWS", "Kubernetes"],
                "hobbies": ["gaming", "music", "cooking"],
                "experience_years": 3,
                "education": "Software Engineering, MIT",
                "bio": "Backend engineer passionate about cloud technologies and microservices.",
                "preferences": {
                    "salary_min": 100000,
                    "salary_max": 140000,
                    "job_type": "full_time",
                    "remote_preference": "remote"
                }
            },
            {
                "user": {
                    "email": "carol.analyst@example.com",
                    "password": "password123",
                    "full_name": "Carol Davis",
                    "phone": "+1-555-0103",
                    "role": UserRole.CANDIDATE
                },
                "location": "Austin, TX",
                "skills": ["Python", "Pandas", "Scikit-learn", "SQL", "Tableau"],
                "hobbies": ["data visualization", "machine learning", "tennis"],
                "experience_years": 4,
                "education": "Data Science, UT Austin",
                "bio": "Data scientist with expertise in machine learning and statistical analysis.",
                "preferences": {
                    "salary_min": 95000,
                    "salary_max": 130000,
                    "job_type": "full_time",
                    "remote_preference": "hybrid"
                }
            }
        ]
        
        created_candidates = []
        for candidate_data in candidates_data:
            try:
                candidate_create = CandidateCreate(**candidate_data)
                candidate = await candidate_service.create_candidate(candidate_create)
                created_candidates.append(candidate)
                print(f"Created candidate: {candidate.user.full_name} ({candidate.user.email})")
            except Exception as e:
                print(f"Error creating candidate {candidate_data['user']['email']}: {str(e)}")
        
        return created_candidates


async def create_sample_employers():
    """Create sample employers."""
    async with AsyncSessionLocal() as db:
        employer_service = EmployerService(db)
        
        employers_data = [
            {
                "user": {
                    "email": "hr@techstartup.com",
                    "password": "password123",
                    "full_name": "Sarah Williams",
                    "phone": "+1-555-0201",
                    "role": UserRole.EMPLOYER
                },
                "company_name": "TechStartup Inc",
                "company_description": "Fast-growing startup building innovative SaaS solutions.",
                "website": "https://techstartup.com",
                "industry": "Technology",
                "size": "startup",
                "location": "San Francisco, CA"
            },
            {
                "user": {
                    "email": "talent@megacorp.com",
                    "password": "password123",
                    "full_name": "Michael Brown",
                    "phone": "+1-555-0202",
                    "role": UserRole.EMPLOYER
                },
                "company_name": "MegaCorp Solutions",
                "company_description": "Global enterprise software company serving Fortune 500 clients.",
                "website": "https://megacorp.com",
                "industry": "Enterprise Software",
                "size": "large",
                "location": "New York, NY"
            },
            {
                "user": {
                    "email": "hiring@datacompany.com",
                    "password": "password123",
                    "full_name": "Jennifer Lee",
                    "phone": "+1-555-0203",
                    "role": UserRole.EMPLOYER
                },
                "company_name": "Data Insights Co",
                "company_description": "Data analytics company helping businesses make data-driven decisions.",
                "website": "https://datainsights.com",
                "industry": "Data Analytics",
                "size": "medium",
                "location": "Austin, TX"
            }
        ]
        
        created_employers = []
        for employer_data in employers_data:
            try:
                employer_create = EmployerCreate(**employer_data)
                employer = await employer_service.create_employer(employer_create)
                created_employers.append(employer)
                print(f"Created employer: {employer.company_name} ({employer.user.email})")
            except Exception as e:
                print(f"Error creating employer {employer_data['user']['email']}: {str(e)}")
        
        return created_employers


async def create_sample_jobs(employers):
    """Create sample jobs."""
    async with AsyncSessionLocal() as db:
        job_service = JobService(db)
        
        jobs_data = [
            {
                "employer_id": employers[0].user.id,  # TechStartup Inc
                "title": "Senior Full-Stack Developer",
                "description": """We're looking for a senior full-stack developer to join our growing team. 
                You'll work on building scalable web applications using modern technologies.
                
                Responsibilities:
                - Design and develop web applications using Python/FastAPI and React
                - Collaborate with product and design teams
                - Mentor junior developers
                - Participate in architecture decisions
                
                Requirements:
                - 4+ years of experience with Python and JavaScript
                - Experience with FastAPI or similar frameworks
                - Strong knowledge of databases (PostgreSQL preferred)
                - Experience with cloud platforms (AWS/GCP)""",
                "company": "TechStartup Inc",
                "location": "San Francisco, CA",
                "required_skills": ["Python", "FastAPI", "React", "PostgreSQL", "AWS"],
                "nice_to_have_skills": ["Docker", "Kubernetes", "Redis"],
                "salary_min": 130000,
                "salary_max": 170000,
                "currency": "USD",
                "job_type": JobType.FULL_TIME,
                "remote_allowed": "hybrid",
                "experience_min": 4,
                "experience_max": 8,
                "benefits": ["health_insurance", "401k", "unlimited_pto", "stock_options"],
                "application_email": "hr@techstartup.com"
            },
            {
                "employer_id": employers[1].user.id,  # MegaCorp Solutions
                "title": "Backend Engineer",
                "description": """Join our backend engineering team to build enterprise-grade solutions.
                
                You'll work on:
                - Microservices architecture
                - API design and development
                - Database optimization
                - System scalability
                
                Requirements:
                - 3+ years of backend development experience
                - Strong knowledge of Node.js or Python
                - Experience with microservices
                - Database design and optimization skills""",
                "company": "MegaCorp Solutions",
                "location": "New York, NY",
                "required_skills": ["Node.js", "MongoDB", "AWS", "Microservices"],
                "nice_to_have_skills": ["Kubernetes", "GraphQL", "RabbitMQ"],
                "salary_min": 110000,
                "salary_max": 150000,
                "currency": "USD",
                "job_type": JobType.FULL_TIME,
                "remote_allowed": "remote",
                "experience_min": 3,
                "experience_max": 6,
                "benefits": ["health_insurance", "401k", "professional_development"],
                "application_email": "talent@megacorp.com"
            },
            {
                "employer_id": employers[2].user.id,  # Data Insights Co
                "title": "Data Scientist",
                "description": """We're seeking a data scientist to help our clients extract insights from their data.
                
                What you'll do:
                - Build machine learning models
                - Perform statistical analysis
                - Create data visualizations
                - Work with clients to understand their needs
                
                Requirements:
                - Advanced degree in Data Science, Statistics, or related field
                - 3+ years of experience with Python for data science
                - Strong knowledge of ML libraries (scikit-learn, pandas)
                - Experience with data visualization tools""",
                "company": "Data Insights Co",
                "location": "Austin, TX",
                "required_skills": ["Python", "Pandas", "Scikit-learn", "SQL", "Statistics"],
                "nice_to_have_skills": ["TensorFlow", "Tableau", "R", "Spark"],
                "salary_min": 100000,
                "salary_max": 135000,
                "currency": "USD",
                "job_type": JobType.FULL_TIME,
                "remote_allowed": "hybrid",
                "experience_min": 3,
                "experience_max": 7,
                "benefits": ["health_insurance", "401k", "flexible_hours"],
                "application_email": "hiring@datacompany.com"
            }
        ]
        
        created_jobs = []
        for job_data in jobs_data:
            try:
                job_create = JobCreate(**{k: v for k, v in job_data.items() if k != 'employer_id'})
                job = await job_service.create_job(job_create, job_data['employer_id'])
                created_jobs.append(job)
                print(f"Created job: {job.title} at {job.company}")
            except Exception as e:
                print(f"Error creating job {job_data['title']}: {str(e)}")
        
        return created_jobs


async def main():
    """Main seeding function."""
    print("🌱 Starting database seeding...")
    
    try:
        # Create sample data
        print("\n📝 Creating sample candidates...")
        candidates = await create_sample_candidates()
        
        print("\n🏢 Creating sample employers...")
        employers = await create_sample_employers()
        
        print("\n💼 Creating sample jobs...")
        jobs = await create_sample_jobs(employers)
        
        print(f"\n✅ Seeding completed successfully!")
        print(f"   - Created {len(candidates)} candidates")
        print(f"   - Created {len(employers)} employers")
        print(f"   - Created {len(jobs)} jobs")
        
        print("\n📧 Sample login credentials:")
        print("Candidates:")
        print("  - alice.developer@example.com / password123")
        print("  - bob.engineer@example.com / password123")
        print("  - carol.analyst@example.com / password123")
        print("\nEmployers:")
        print("  - hr@techstartup.com / password123")
        print("  - talent@megacorp.com / password123")
        print("  - hiring@datacompany.com / password123")
        
    except Exception as e:
        print(f"❌ Error during seeding: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
