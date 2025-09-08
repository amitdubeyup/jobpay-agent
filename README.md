# JobPay Agent - AI-Powered Job Matching Platform

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A production-grade AI-powered job matching platform built with FastAPI, PostgreSQL, and LangChain. The platform intelligently matches candidates with job opportunities using semantic analysis and machine learning.

## 🚀 Features

### Core Functionality
- **AI-Powered Matching**: Uses LangChain and OpenAI embeddings for intelligent job-candidate matching
- **Real-time Notifications**: Multi-channel notifications (Email, SMS, WhatsApp, Push)
- **Role-based Access**: Separate interfaces for candidates and employers
- **Background Processing**: Asynchronous job matching and notification delivery
- **Comprehensive API**: RESTful API with OpenAPI documentation

### Technical Features
- **Production Ready**: Docker containerization, comprehensive testing, monitoring
- **Scalable Architecture**: Async database operations, background workers, caching
- **Security**: JWT authentication, role-based access control, input validation
- **Developer Experience**: Pre-commit hooks, linting, formatting, type hints

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │  Celery Workers │    │   PostgreSQL    │
│                 │    │                 │    │                 │
│ • REST API      │    │ • Job Matching  │    │ • User Data     │
│ • Authentication│    │ • Notifications │    │ • Jobs & Matches│
│ • Validation    │    │ • Background    │    │ • Audit Logs    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │      Redis      │
                    │                 │
                    │ • Queue Broker  │
                    │ • Caching       │
                    │ • Sessions      │
                    └─────────────────┘
```

## 📋 Prerequisites

- Python 3.11+
- Docker and Docker Compose
- PostgreSQL 15+
- Redis 7+
- OpenAI API Key (for AI matching)

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone <repository-url>
cd jobpay-agent
```

### 2. Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
# Required: OPENAI_API_KEY, SMTP settings, Twilio credentials
```

### 3. Docker Development Setup
```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f api
```

### 4. Database Setup
```bash
# Run migrations
docker-compose exec api alembic upgrade head

# Seed sample data
docker-compose exec api python scripts/seed_data.py
```

### 5. Access the Application
- **API Documentation**: http://localhost:8000/api/v1/docs
- **Application**: http://localhost:8000
- **Flower (Celery Monitor)**: http://localhost:5555

## 📚 API Documentation

### Authentication
```bash
# Login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=alice.developer@example.com&password=password123"
```

### Create Candidate
```bash
curl -X POST "http://localhost:8000/api/v1/users/candidates" \
  -H "Content-Type: application/json" \
  -d '{
    "user": {
      "email": "john@example.com",
      "password": "password123",
      "full_name": "John Doe",
      "role": "candidate"
    },
    "skills": ["Python", "FastAPI"],
    "location": "San Francisco, CA"
  }'
```

### Create Job
```bash
curl -X POST "http://localhost:8000/api/v1/jobs" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Senior Python Developer",
    "description": "We are looking for...",
    "company": "TechCorp",
    "required_skills": ["Python", "FastAPI", "PostgreSQL"],
    "salary_min": 120000,
    "salary_max": 160000
  }'
```

### Search Jobs
```bash
curl "http://localhost:8000/api/v1/jobs?skills=Python,FastAPI&location=San Francisco"
```

## 🔧 Development

### Local Setup (without Docker)
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your settings

# Start PostgreSQL and Redis locally
# Then run migrations
alembic upgrade head

# Start the application
uvicorn app.main:app --reload

# In separate terminals, start workers
celery -A app.workers.celery_app worker --loglevel=info
celery -A app.workers.celery_app beat --loglevel=info
```

### Code Quality
```bash
# Install pre-commit hooks
pre-commit install

# Run linting and formatting
black .
isort .
flake8 .
mypy .

# Run tests
pytest
pytest --cov=app tests/
```

### Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_auth.py

# Run tests with verbose output
pytest -v

# Run only fast tests (exclude slow/integration tests)
pytest -m "not slow"
```

## 📊 Monitoring

### Application Health
- Health check: `GET /health`
- Metrics: `GET /metrics` (if implemented)

### Celery Monitoring
- Flower dashboard: http://localhost:5555
- Task monitoring, worker status, queue inspection

### Database Monitoring
```bash
# Check database connections
docker-compose exec db psql -U postgres -d jobpay_agent -c "SELECT count(*) FROM pg_stat_activity;"

# Monitor Redis
docker-compose exec redis redis-cli monitor
```

## 🚀 Deployment

### Production Configuration
1. **Environment Variables**: Set all required production values
2. **Database**: Use managed PostgreSQL service
3. **Redis**: Use managed Redis service  
4. **SSL/TLS**: Configure HTTPS
5. **Monitoring**: Set up logging and monitoring
6. **Backup**: Configure database backups

### Docker Production Build
```bash
# Build production image
docker build -t jobpay-agent:prod .

# Run with production compose file
docker-compose -f docker-compose.prod.yml up -d
```

### Kubernetes Deployment
```bash
# Apply Kubernetes manifests (if available)
kubectl apply -f k8s/
```

## 📈 Scaling

### Horizontal Scaling
- **API**: Scale FastAPI instances behind load balancer
- **Workers**: Scale Celery workers based on queue length
- **Database**: Use read replicas for read-heavy operations

### Performance Optimization
- **Caching**: Redis for frequently accessed data
- **Database**: Optimize queries, add indexes
- **Background Jobs**: Tune worker concurrency
- **CDN**: Use CDN for static assets

## 🔒 Security

### Authentication & Authorization
- JWT tokens with expiration
- Role-based access control
- Password hashing with bcrypt

### API Security
- Input validation with Pydantic
- SQL injection protection (SQLAlchemy)
- Rate limiting
- CORS configuration

### Infrastructure Security
- Environment variable management
- Database connection encryption
- Regular security updates

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guide
- Write comprehensive tests
- Update documentation
- Use pre-commit hooks

## 📝 Sample Data

The application includes a seed script with sample data:

### Sample Candidates
- **alice.developer@example.com** / password123
- **bob.engineer@example.com** / password123  
- **carol.analyst@example.com** / password123

### Sample Employers
- **hr@techstartup.com** / password123
- **talent@megacorp.com** / password123
- **hiring@datacompany.com** / password123

## 🛠️ Technology Stack

### Backend
- **FastAPI**: Modern, fast web framework
- **SQLAlchemy**: SQL toolkit and ORM
- **Alembic**: Database migration tool
- **Pydantic**: Data validation and settings

### AI/ML
- **LangChain**: LLM application framework
- **OpenAI**: GPT models and embeddings
- **Sentence Transformers**: Semantic similarity

### Database & Cache
- **PostgreSQL**: Primary database
- **Redis**: Cache and message broker

### Background Jobs
- **Celery**: Distributed task queue
- **Flower**: Celery monitoring

### Notifications
- **SMTP**: Email notifications
- **Twilio**: SMS and WhatsApp
- **Firebase**: Push notifications

### Development Tools
- **Docker**: Containerization
- **pytest**: Testing framework
- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking
- **pre-commit**: Git hooks

## 📞 Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the API docs at `/api/v1/docs`

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- FastAPI team for the excellent framework
- LangChain community for AI/ML tools
- Open source contributors

---

**Built with ❤️ for the future of job matching**
