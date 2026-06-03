# AI-Powered Student Information System

A production-grade, multi-tenant SIS built with FastAPI, LangGraph, Claude API, and Supabase.

**Live Demo:** https://sis.datawebify.com  
**API Docs:** https://sis.datawebify.com/docs  
**Built by:** [Datawebify](https://datawebify.com)

## Stack
- Backend: Python, FastAPI, LangGraph, SQLAlchemy
- AI: Anthropic Claude API (primary), GPT-4o (fallback)
- Database: Supabase / PostgreSQL with Row Level Security
- Vector Store: Pinecone (RAG pipeline)
- Deployment: Docker, Railway

## Setup

```bash
git clone https://github.com/umair801/sis-agent.git
cd sis-agent/backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env         # Fill in your credentials
uvicorn app.main:app --reload --port 8000
```

## Modules
- Multi-tenant architecture with JWT + RBAC
- Student profiles and enrollment
- Attendance tracking (daily + period-level)
- Scheduling engine with conflict detection
- Gradebook and transcript generation
- SpEd / IEP management
- Budget forecasting
- Parent communication portal
- Claude AI embedded in every module