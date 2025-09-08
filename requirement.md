You are my backend coding assistant.  
I want to build an AI-powered job matching agent with the following stack and production-grade practices:

---

### Tech Stack
- **Backend Framework:** FastAPI (Python, async)
- **Database:** PostgreSQL (SQLAlchemy ORM with Alembic migrations)
- **AI/LLM Tools:** LangChain (for requirement/skill analysis + semantic matching)
- **Queue/Background Jobs:** Celery or RQ with Redis
- **Notifications:** Email, SMS, Push, WhatsApp (pluggable provider architecture)
- **Config:** dotenv or Pydantic Settings for environment variables
- **Testing:** pytest + coverage
- **Code Quality:** flake8, black, isort, mypy, pre-commit hooks
- **Docs:** OpenAPI auto-docs, README, docstrings
- **Deployment Ready:** Docker + docker-compose

---

### Features
1. **User & Job Models**
   - Candidate: id, name, email, phone, location, skills (list/JSONB), hobbies, preferences
   - Job: id, title, description, location, required_skills (list/JSONB), company, salary_range, job_type
   - NotificationPreference: candidate_id, channels (email/sms/push/whatsapp/webpush)

2. **Job Posting Flow**
   - Employers can post jobs via REST API
   - Each job triggers background task → AI matching → notify candidates

3. **Matching Agent**
   - Use LangChain embeddings + semantic similarity for skills/hobbies/requirements
   - Filter by location + preferences
   - Rank candidates by relevance score
   - Log match scores for audit/debug

4. **Notification System**
   - Unified notification service layer
   - Providers: Email (SMTP), SMS (Twilio), WhatsApp (Twilio WhatsApp), Push (Firebase/WebPush)
   - Send async notifications via queue workers
   - Templated messages with job info + application link

5. **Background Jobs**
   - Workflow:
     - Job created → enqueue matching task
     - Matching task → find candidates + enqueue notifications
   - Workers run independently from API

6. **APIs**
   - POST /candidates → register candidate
   - POST /jobs → create new job
   - GET /matches/{candidate_id} → fetch candidate’s matched jobs
   - (Optional) Webhook endpoint for external notification services

---

### Production Grade Requirements
- **Security**
  - JWT authentication (FastAPI OAuth2 + refresh tokens)
  - Role-based access control (candidate vs employer)
  - Input validation with Pydantic
  - SQL injection/XSS safe defaults
  - Rate limiting + CORS settings

- **Scalability & Optimization**
  - Use async DB queries
  - Index frequently queried fields (skills, location)
  - Redis caching for match results
  - Pagination for large responses
  - Configurable worker concurrency

- **Tests**
  - Unit tests for services, models, notifications
  - Integration tests for API endpoints
  - Mock external services (email/sms)
  - CI pipeline with coverage threshold

- **Developer Experience**
  - Pre-commit hooks (black, isort, flake8, mypy)
  - Dockerized local dev setup
  - Seed data script for demo/testing
  - Linting + formatting enforced in CI

---

### Output
Generate a **full backend scaffold** with:
- Clean project structure (routes, services, models, db, notifications, workers, tests)
- Secure authentication & role system
- Job posting & matching workflow
- Notification system with pluggable providers
- Background worker setup
- AI matching service (LangChain integration)
- Tests & sample data
- Linting + Docker configs
