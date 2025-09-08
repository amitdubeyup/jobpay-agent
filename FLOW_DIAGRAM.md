# 🌊 JobPay Agent - Request Flow Architecture

## 🏗️ **Complete Request Lifecycle**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                               🌐 CLIENT REQUEST                             │
│                         (HTTP/HTTPS to http://api.com)                     │
└─────────────────────────┬───────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────────────┐
│                          🚪 FASTAPI APPLICATION                             │
│                            app/main.py                                      │
│                                                                             │
│  📋 Request Entry Point                                                     │
│  • CORS Validation                                                          │
│  • Trusted Host Check                                                       │
│  • Initial Request Processing                                               │
└─────────────────────────┬───────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────────────┐
│                       🛡️ MIDDLEWARE STACK                                   │
│                      (Executed in REVERSE order)                           │
│                                                                             │
│  1️⃣ ErrorHandlingMiddleware     📋 Exception handling & error responses     │
│     └─ app/middleware/error_handling.py                                    │
│                                                                             │
│  2️⃣ MetricsMiddleware           📊 Performance & usage tracking            │
│     └─ app/middleware/metrics.py                                           │
│                                                                             │
│  3️⃣ RequestLoggingMiddleware    📝 Request/response logging               │
│     └─ app/middleware/request_logging.py                                   │
│                                                                             │
│  4️⃣ RateLimitMiddleware         ⚡ API rate limiting & protection          │
│     └─ app/middleware/rate_limiting.py                                     │
│                                                                             │
│  5️⃣ CORSMiddleware             🌐 Cross-origin request handling            │
│     └─ FastAPI built-in                                                    │
│                                                                             │
│  6️⃣ TrustedHostMiddleware      🔒 Host validation & security              │
│     └─ FastAPI built-in                                                    │
└─────────────────────────┬───────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────────────┐
│                        🎯 ROUTING LAYER                                     │
│                       app/api/__init__.py                                   │
│                                                                             │
│  📍 Route Resolution:                                                       │
│                                                                             │
│  🌐 /api/health          → Health Checks                                   │
│  🌐 /api/metrics         → System Metrics                                  │
│  🌐 /api/version         → API Version Info                                │
│  🌐 /api/v1/*           → Versioned API Routes                             │
└─────────────────────────┬───────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────────────┐
│                      📡 API v1 ROUTER                                       │
│                     app/api/v1/__init__.py                                  │
│                                                                             │
│  🔗 Route Distribution:                                                     │
│                                                                             │
│  🔐 /api/v1/auth/*       → Authentication endpoints                        │
│  👥 /api/v1/users/*      → User management                                 │
│  💼 /api/v1/jobs/*       → Job operations                                  │
│  🔔 /api/v1/notifications/* → Notification handling                        │
└─────────────────────────┬───────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────────────┐
│                     🎯 ENDPOINT HANDLER                                     │
│                 app/api/v1/{module}.py                                      │
│                                                                             │
│  🔍 Example: POST /api/v1/jobs                                             │
│  📄 File: app/api/v1/jobs.py                                               │
│  ⚙️ Function: create_job()                                                  │
│                                                                             │
│  📋 Processing Steps:                                                       │
│  1. Request validation (Pydantic schemas)                                  │
│  2. Authentication check (JWT token)                                       │
│  3. Authorization check (role-based)                                       │
│  4. Input validation & sanitization                                        │
│  5. Business logic execution                                               │
└─────────────────────────┬───────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────────────┐
│                      🔒 SECURITY LAYER                                      │
│                     app/core/security.py                                    │
│                                                                             │
│  🎫 Authentication Flow:                                                    │
│  1. Extract JWT token from Authorization header                            │
│  2. Validate token signature & expiration                                  │
│  3. Decode user information                                                 │
│  4. Check user status (active/inactive)                                    │
│  5. Role-based access control                                              │
│                                                                             │
│  🛡️ Security Dependencies:                                                  │
│  • get_current_user()                                                      │
│  • get_current_active_user()                                               │
│  • require_role(UserRole.EMPLOYER)                                         │
└─────────────────────────┬───────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────────────┐
│                     📊 SERVICE LAYER                                        │
│                    app/services/*.py                                        │
│                                                                             │
│  🔧 Business Logic Services:                                               │
│                                                                             │
│  👤 UserService          → User management operations                      │
│  💼 JobService           → Job CRUD & search operations                    │
│  🤖 AIMatchingService    → LangChain-powered job matching                  │
│  🔔 NotificationService  → Multi-channel notifications                     │
│                                                                             │
│  📋 Service Responsibilities:                                               │
│  • Business rule enforcement                                               │
│  • Data validation & transformation                                        │
│  • External service integration                                            │
│  • Complex query operations                                                │
└─────────────────────────┬───────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────────────┐
│                     💾 DATA ACCESS LAYER                                    │
│                                                                             │
│  🗄️ Database Operations:                                                    │
│                                                                             │
│  📊 PostgreSQL (Primary)    → app/models/*.py                             │
│  ├─ User models                                                            │
│  ├─ Job models                                                             │
│  ├─ Notification models                                                     │
│  └─ JobMatch models                                                         │
│                                                                             │
│  ⚡ Redis Cache             → app/cache/manager.py                         │
│  ├─ Session storage                                                         │
│  ├─ Rate limiting counters                                                  │
│  ├─ Cached query results                                                    │
│  └─ Background job queues                                                   │
└─────────────────────────┬───────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────────────┐
│                    🔄 BACKGROUND PROCESSING                                 │
│                                                                             │
│  ⚙️ Celery Task Queue:                                                      │
│                                                                             │
│  🤖 AI Matching Tasks        → app/workers/matching_tasks.py               │
│  ├─ process_job_matching()                                                  │
│  ├─ find_candidate_matches()                                                │
│  └─ calculate_match_scores()                                                │
│                                                                             │
│  🔔 Notification Tasks      → app/workers/notification_tasks.py            │
│  ├─ send_email_notification()                                              │
│  ├─ send_sms_notification()                                                 │
│  └─ send_push_notification()                                                │
└─────────────────────────┬───────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────────────┐
│                   🧠 AI PROCESSING LAYER                                    │
│                                                                             │
│  🤖 LangChain Integration:                                                  │
│                                                                             │
│  📊 OpenAI Embeddings       → Semantic skill matching                      │
│  🧠 ChatGPT Integration     → Match reasoning & explanations               │
│  🔍 Vector Search           → FAISS similarity search                      │
│  📈 Scoring Algorithms      → Multi-dimensional compatibility              │
│                                                                             │
│  🎯 AI Workflow:                                                            │
│  1. Extract job requirements                                                │
│  2. Generate embeddings for skills                                         │
│  3. Search candidate database                                              │
│  4. Calculate compatibility scores                                         │
│  5. Generate match explanations                                            │
│  6. Rank and return results                                                │
└─────────────────────────┬───────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────────────┐
│                     📈 MONITORING & METRICS                                 │
│                                                                             │
│  📊 Performance Tracking:                                                   │
│                                                                             │
│  🔍 Request Metrics         → Response times, status codes                 │
│  💾 System Metrics          → CPU, memory, disk usage                      │
│  🚨 Error Tracking          → Exception logging & alerting                 │
│  🏥 Health Monitoring       → Service dependency checks                    │
│                                                                             │
│  📋 Metrics Collection:                                                     │
│  • app/monitoring/metrics.py                                               │
│  • app/middleware/metrics.py                                               │
│  • Endpoint: /api/metrics                                                  │
└─────────────────────────┬───────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────────────┐
│                       📤 RESPONSE GENERATION                                │
│                                                                             │
│  🔄 Response Pipeline:                                                      │
│                                                                             │
│  1️⃣ Data Serialization      → Pydantic models to JSON                     │
│  2️⃣ Response Headers        → CORS, timing, cache headers                 │
│  3️⃣ Status Code Setting     → HTTP status codes                           │
│  4️⃣ Middleware Processing   → Metrics, logging (reverse order)            │
│  5️⃣ Final Response          → JSON back to client                         │
│                                                                             │
│  📋 Response Format:                                                        │
│  {                                                                          │
│    "data": {...},                                                           │
│    "status": "success",                                                     │
│    "timestamp": "2025-09-08T...",                                          │
│    "request_id": "uuid"                                                     │
│  }                                                                          │
└─────────────────────────┬───────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────────────┐
│                        🌐 CLIENT RESPONSE                                   │
│                          (JSON Response)                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 🎯 **Request Flow Examples**

### **Example 1: Create Job** (`POST /api/v1/jobs`)

```
Client Request → CORS Check → Rate Limiting → Request Logging →
Authentication → Authorization (Employer role) → Input Validation →
JobService.create_job() → Database Insert → AI Matching Queue →
Notification Queue → Response Generation → Client
```

### **Example 2: Search Jobs** (`GET /api/v1/jobs`)

```
Client Request → Middleware Stack → Route Resolution →
Query Parameter Validation → JobService.search_jobs() →
Database Query → Cache Check → Response Serialization → Client
```

### **Example 3: AI Job Matching** (Background)

```
Job Created → Celery Task Queued → AIMatchingService →
LangChain Processing → OpenAI API → Vector Similarity →
Score Calculation → Match Storage → Notification Queue
```

## 🔧 **Key Architecture Patterns**

### **1. Layered Architecture**
- **Presentation**: FastAPI routes & middleware
- **Business**: Service layer with business logic
- **Data**: Models, repositories, cache
- **Integration**: External APIs, AI services

### **2. Dependency Injection**
- Database sessions via `Depends(get_db)`
- Authentication via `Depends(get_current_user)`
- Role-based access via `require_role()`

### **3. Async Processing**
- All database operations are async
- Background tasks via Celery
- Non-blocking AI processing

### **4. Error Handling**
- Custom exception hierarchy
- Middleware-based error handling
- Structured error responses

### **5. Monitoring & Observability**
- Request/response logging
- Performance metrics collection
- Health check endpoints
- Distributed tracing ready

This architecture provides **enterprise-grade scalability, maintainability, and performance**! 🚀
