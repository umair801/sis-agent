# SIS Agent — AI-Powered Student Information System

> Built by [Datawebify](https://datawebify.com) · Production deployment: [sis.datawebify.com](https://sis.datawebify.com)

A production-grade, multi-tenant, AI-powered Student Information System (SIS) for K-12 school districts. Built with FastAPI, LangGraph, Claude AI, React, and Supabase. Deployed on Railway.

---

## Live Demo

| Resource | URL |
|----------|-----|
| Frontend Portal | https://sis.datawebify.com |
| API (Live) | https://sis-agent-production.up.railway.app/api/v1/health |
| API Docs (Swagger) | https://sis-agent-production.up.railway.app/docs |
| GitHub | https://github.com/umair801/sis-agent |

**Demo credentials:**

| Role | Email | Password |
|------|-------|----------|
| Super Admin | admin@westlake.edu | admin123 |
| Teacher | teacher@westlake.edu | Password123! |
| Principal | principal@westlake.edu | Password123! |
| SpEd Coordinator | sped@westlake.edu | Password123! |
| Parent | parent@westlake.edu | Password123! |
| District Admin | district@westlake.edu | Password123! |

---

## Overview

This system was built for **Westlake Unified School District** as a full-stack SaaS platform demonstrating:

- Multi-tenant architecture with row-level security
- 6 role-scoped dashboards with distinct permissions
- AI-powered natural language querying across all data modules
- Automated compliance monitoring (IDEA/FERPA)
- LangGraph multi-agent orchestration with Claude as the primary LLM
- RAG pipeline over district documents (Pinecone vector store)

---

## Tech Stack

### Backend
| Layer | Technology |
|-------|-----------|
| Framework | FastAPI 0.136 + Python 3.12 |
| AI Orchestration | LangGraph + LangChain |
| Primary LLM | Anthropic Claude (claude-sonnet-4) |
| Fallback LLM | OpenAI GPT-4o |
| Database | PostgreSQL via Supabase |
| ORM | SQLAlchemy 2.0 (async) |
| Auth | JWT with tenant_id + role claims |
| Vector Store | Pinecone (RAG pipeline) |
| Deployment | Railway (Docker) |

### Frontend
| Layer | Technology |
|-------|-----------|
| Framework | React 18 + Vite |
| Styling | Tailwind CSS |
| Routing | React Router v6 |
| HTTP Client | Axios with JWT interceptors |
| State | React Context + useState |
| Deployment | Railway (Nginx) |

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    React Frontend                        │
│   6 role-scoped dashboards + embedded AI query panel    │
└────────────────────────┬────────────────────────────────┘
                         │ HTTPS
┌────────────────────────▼────────────────────────────────┐
│                  FastAPI Backend                         │
│                 /api/v1 (37 routes)                     │
├─────────────────────────────────────────────────────────┤
│              LangGraph Orchestration                     │
│   Supervisor → [NL Query, Reports, Conflicts,           │
│                 Forecasting, Compliance, RAG]           │
├─────────────────────────────────────────────────────────┤
│           Claude API + GPT-4o (fallback)                │
├─────────────────────────────────────────────────────────┤
│         Supabase PostgreSQL (37 tables, RLS)            │
│                  Pinecone (RAG)                         │
└─────────────────────────────────────────────────────────┘
```

---

## Modules

### Phase B — Education Domain Modules

| Module | Description | Endpoints |
|--------|-------------|-----------|
| B1: Students | Enrollment CRUD, profiles, grade levels | `/api/v1/students` |
| B2: Attendance | Daily + period-level tracking, reports | `/api/v1/attendance` |
| B3: Scheduling | Section/room/teacher assignment, conflict detection | `/api/v1/scheduling` |
| B4: Gradebook | Grade entry, GPA calculation, transcripts | `/api/v1/gradebook` |
| B5: SpEd/IEP | IEP records, deadline tracking, IDEA compliance | `/api/v1/sped` |
| B6: Budget | Resource allocation, fiscal years, forecasting | `/api/v1/budget` |
| B7: Communication | Announcements, parent notifications, messaging | `/api/v1/communication` |

### Phase C — AI Intelligence Layer

| Module | Description | Endpoint |
|--------|-------------|----------|
| C1: NL Query | Natural language to SQL, AI-summarized results | `POST /api/v1/query/ask` |
| C2: Reports | Automated attendance, grade, and compliance reports | `POST /api/v1/reports/generate` |
| C3: Conflict Detection | Scheduling conflicts, IEP deadline alerts | `GET /api/v1/conflicts/scan` |
| C4: Forecasting | Enrollment trends, budget projections | `POST /api/v1/forecasts/run` |
| C5: Compliance | IDEA/FERPA flag detection, audit trail | `GET /api/v1/compliance/check` |
| C6: RAG | Policy lookup, handbook Q&A over district documents | `POST /api/v1/district-docs/query` |

### Phase D — Frontend Dashboards

| Dashboard | Role | Key Features |
|-----------|------|--------------|
| Super Admin | SuperAdmin | Tenant management, system health, user overview |
| District Admin | DistrictAdmin | Student overview, budget, alerts, reports |
| Teacher | Teacher | Attendance entry (mobile-optimized), gradebook, sections |
| SpEd Coordinator | SpEdCoordinator | IEP tracker, compliance alerts, deadline management |
| Principal | Principal | School analytics, attendance trends, grade breakdown |
| Parent Portal | Parent | Child's grades, attendance record, school messages |

All dashboards include an embedded **AI Query Panel** powered by Claude.

---

## Database Schema

37 tables in Supabase PostgreSQL, all with:
- `sis_` prefix for namespace isolation
- `tenant_id` column on every table for multi-tenancy
- Row-Level Security (RLS) policies
- `service_role` bypass policies for backend access

Key tables: `sis_tenant`, `sis_user`, `sis_role`, `sis_student`, `sis_attendance_daily`, `sis_attendance_period`, `sis_section`, `sis_course`, `sis_grade`, `sis_iep`, `sis_budget`, `sis_announcement`, `sis_message`

---

## API Reference

Full interactive API documentation: **https://sis-agent-production.up.railway.app/docs**

### Authentication

All endpoints require a Bearer token obtained from:

```bash
POST /api/v1/auth/login
{
  "email": "admin@westlake.edu",
  "password": "admin123",
  "tenant_slug": "westlake"
}
```

Response includes `access_token`, `role`, `tenant_id`, `full_name`.

### Example: NL Query

```bash
POST /api/v1/query/ask
Authorization: Bearer <token>
{
  "question": "How many students were absent last week?"
}
```

### Example: Run Compliance Check

```bash
GET /api/v1/compliance/check
Authorization: Bearer <token>
```

---

## Role-Based Access Control

| Endpoint Category | SuperAdmin | DistrictAdmin | Principal | Teacher | SpEdCoordinator | Parent |
|------------------|:---:|:---:|:---:|:---:|:---:|:---:|
| Students | R/W | R/W | R | R | R | - |
| Attendance | R/W | R/W | R/W | R/W | R | - |
| Scheduling | R/W | R/W | R/W | R | R | - |
| Gradebook | R/W | R/W | R/W | R/W | R | - |
| SpEd/IEP | R/W | R/W | R | - | R/W | - |
| Budget | R/W | R/W | R | - | - | - |
| Communication | R/W | R/W | R/W | R/W | R/W | R/W |
| AI Query | R/W | R/W | R/W | R/W | R/W | R/W |

---

## Local Development

### Prerequisites
- Python 3.12+
- Node.js 20+
- Supabase account
- Anthropic API key
- Pinecone account

### Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
cp .env.example .env            # Fill in your credentials
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
# Create .env with: VITE_API_URL=/api/v1
npm run dev
```

### Docker (full stack)

```bash
docker compose up --build
# Frontend: http://localhost
# Backend:  http://localhost:8000
```

---

## Project Structure

```
sis-agent/
├── backend/
│   ├── app/
│   │   ├── api/v1/routes/      # 18 route files
│   │   ├── agents/             # LangGraph orchestration
│   │   ├── models/             # SQLAlchemy models (37 tables)
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   ├── services/           # Business logic layer
│   │   ├── rag/                # RAG pipeline (Pinecone)
│   │   └── core/               # Config, auth, logging
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/                # Axios API clients
│   │   ├── components/         # Reusable UI + AI panel
│   │   ├── contexts/           # AuthContext
│   │   ├── pages/              # 6 role dashboards
│   │   └── utils/
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml
└── README.md
```

---

## Business Metrics (Demo District)

| Metric | Value |
|--------|-------|
| Students enrolled | 452 |
| Active IEPs | 5 |
| Attendance rate | 94.4% |
| API endpoints | 41 tested, 100% pass rate |
| Roles supported | 6 |
| Database tables | 37 |
| AI modules | 6 (NL query, reports, conflicts, forecasting, compliance, RAG) |

---

## Built By

**Datawebify** — Agentic AI systems for enterprise clients.

- Website: [datawebify.com](https://datawebify.com)
- GitHub: [github.com/umair801](https://github.com/umair801)
- Upwork: [upwork.com/freelancers/umair801](https://upwork.com/freelancers/umair801)

---

## License

This project is a portfolio demonstration system built by Datawebify.
