# Upwork Proposal Template — Student Information System / EdTech SaaS
# Use for jobs matching: SIS, school management, EdTech, K-12 platform,
# student data management, attendance system, IEP management, school ERP

---

## PROPOSAL (adapt to each job posting)

Subject: Built a production SIS with AI compliance monitoring — live demo ready

---

I just finished building an AI-powered Student Information System for a K-12
school district. It is live at sis.datawebify.com and covers exactly what you
are describing.

Here is what the system does:

- Attendance tracking (daily + period-level) with automated absence alerts
- Gradebook with GPA calculation and transcript export
- IEP and SpEd module with IDEA/FERPA compliance monitoring and deadline alerts
- Scheduling engine with conflict detection
- Budget module with scenario forecasting
- Parent portal with grades, attendance, and direct messaging
- Natural language querying — staff can ask "which students missed more than
  3 days this month?" and get an AI-generated answer instantly
- 6 role-scoped dashboards: SuperAdmin, DistrictAdmin, Principal, Teacher,
  SpEd Coordinator, Parent

The AI layer uses Claude (Anthropic) as the primary LLM with GPT-4o as fallback,
LangGraph for multi-agent orchestration, and a RAG pipeline over district policy
documents using Pinecone.

Tech stack: Python, FastAPI, LangGraph, Claude API, PostgreSQL (Supabase),
React, Tailwind, Docker, Railway.

Live demo: https://sis.datawebify.com
Login: admin@westlake.edu / admin123 (SuperAdmin role)
API docs: https://sis-agent-production.up.railway.app/docs

I can adapt this system to your district's specific requirements or build a
custom version from scratch depending on your needs. Happy to jump on a call
to walk through the demo.

---

## SCREENING QUESTIONS TO WATCH FOR
- Do you have experience with multi-tenant SaaS? YES — show the tenant isolation code
- Have you worked with school data or FERPA? YES — C5 compliance module
- Can you show similar work? YES — live demo at sis.datawebify.com
- What is your timeline? Depends on scope — existing modules can be adapted in 1-2 weeks

## JOBS TO SEARCH
- "student information system"
- "school management system"
- "attendance tracking system"
- "IEP management system"
- "K-12 SaaS platform"
- "edtech backend developer"
- "school ERP FastAPI"
- "student data management system"
