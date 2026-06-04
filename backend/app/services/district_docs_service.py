"""
C6 -- RAG over District Documents
Education-domain wrapper over the existing RAG pipeline.
Supports policy lookup, handbook Q&A, IEP context retrieval,
and role-scoped document access.
"""

import anthropic
from typing import Optional
from datetime import datetime

from app.rag.vector_store import similarity_search
from app.core.config import settings
from app.core.logging import logger


# ---------------------------------------------------------------------------
# Document category definitions
# ---------------------------------------------------------------------------

DOC_CATEGORIES = {
    "policy":       "District policies, board rules, administrative regulations",
    "handbook":     "Student and staff handbooks",
    "iep_template": "IEP templates, SpEd procedures, disability category guides",
    "compliance":   "IDEA, FERPA, Section 504 compliance guides",
    "curriculum":   "Curriculum guides, instructional materials, course syllabi",
    "hr":           "Staff employment policies, contracts, evaluation procedures",
    "budget":       "Budget guidelines, expenditure policies, grant documentation",
    "general":      "General district documents and miscellaneous materials",
}

# Role-based document access: which categories each role can query
ROLE_DOC_ACCESS = {
    "SuperAdmin":       list(DOC_CATEGORIES.keys()),
    "DistrictAdmin":    list(DOC_CATEGORIES.keys()),
    "Principal":        ["policy", "handbook", "compliance", "curriculum", "hr", "budget", "general"],
    "Teacher":          ["policy", "handbook", "curriculum", "general"],
    "SpEdCoordinator":  ["policy", "handbook", "iep_template", "compliance", "general"],
    "Parent":           ["handbook", "general"],
}

# System prompts per role
ROLE_SYSTEM_PROMPTS = {
    "SuperAdmin": (
        "You are an expert assistant for the Westlake Unified School District. "
        "Answer questions based ONLY on the provided document context. "
        "Always cite sources using [Source N: document_name] notation. "
        "Be precise and comprehensive. No em-dashes."
    ),
    "DistrictAdmin": (
        "You are an expert district administration assistant. "
        "Answer questions based ONLY on the provided document context. "
        "Cite sources clearly. Focus on administrative and policy implications. No em-dashes."
    ),
    "Principal": (
        "You are a school administration assistant. "
        "Answer questions based ONLY on the provided document context. "
        "Cite sources clearly. Focus on practical school-level implementation. No em-dashes."
    ),
    "Teacher": (
        "You are a helpful assistant for Westlake Unified teachers. "
        "Answer questions based ONLY on the provided document context. "
        "Keep answers practical and classroom-relevant. Cite sources. No em-dashes."
    ),
    "SpEdCoordinator": (
        "You are a special education compliance assistant. "
        "Answer questions based ONLY on the provided document context. "
        "Prioritize IDEA compliance, IEP procedures, and disability law. "
        "Cite sources with regulatory references where applicable. No em-dashes."
    ),
    "Parent": (
        "You are a helpful school information assistant for parents. "
        "Answer questions based ONLY on the provided document context. "
        "Use clear, jargon-free language. Cite the source document. No em-dashes."
    ),
}


# ---------------------------------------------------------------------------
# Main query function
# ---------------------------------------------------------------------------

async def query_district_docs(
    question: str,
    tenant_id: str,
    user_role: str,
    doc_category: Optional[str] = None,
    k: int = 5,
) -> dict:
    """
    Query district documents using RAG.
    Applies role-scoped access, optional category filtering,
    and generates a cited answer using Claude.
    """
    started_at = datetime.utcnow()
    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    # Validate category access
    allowed_categories = ROLE_DOC_ACCESS.get(user_role, ["handbook", "general"])

    if doc_category and doc_category not in DOC_CATEGORIES:
        return {
            "success": False,
            "question": question,
            "answer": f"Unknown document category: {doc_category}. "
                      f"Valid categories: {list(DOC_CATEGORIES.keys())}",
            "citations": [],
            "sources_used": 0,
        }

    if doc_category and doc_category not in allowed_categories:
        return {
            "success": False,
            "question": question,
            "answer": f"Your role ({user_role}) does not have access to '{doc_category}' documents.",
            "citations": [],
            "sources_used": 0,
        }

    # Build namespace: use tenant-scoped namespace from A7
    namespace = f"sis-{tenant_id[:8]}"

    # Retrieve relevant chunks
    try:
        docs = await similarity_search(
            query=question,
            tenant_id=tenant_id,
            k=k,
        )
    except Exception as exc:
        logger.error(f"Vector search failed: {exc}")
        return {
            "success": False,
            "question": question,
            "answer": "Document search is temporarily unavailable. Please try again.",
            "citations": [],
            "sources_used": 0,
            "error": str(exc),
        }

    # Filter by category if specified
    if doc_category:
        docs = [d for d in docs if d.get("doc_type") == doc_category]

    if not docs:
        return {
            "success": True,
            "question": question,
            "answer": (
                "No relevant documents were found for your question"
                + (f" in the '{doc_category}' category" if doc_category else "")
                + ". Please upload relevant district documents first, or try rephrasing your question."
            ),
            "citations": [],
            "sources_used": 0,
            "duration_ms": int((datetime.utcnow() - started_at).total_seconds() * 1000),
        }

    # Build context
    context_parts = []
    for i, doc in enumerate(docs, 1):
        context_parts.append(
            f"[Source {i}: {doc.get('source', 'Unknown')}]\n"
            f"Category: {doc.get('doc_type', 'general')}\n"
            f"Content: {doc.get('content', '')}"
        )
    context = "\n\n---\n\n".join(context_parts)

    system_prompt = ROLE_SYSTEM_PROMPTS.get(user_role, ROLE_SYSTEM_PROMPTS["Teacher"])

    user_message = (
        f"Question: {question}\n\n"
        f"Document Context:\n{context}\n\n"
        f"Provide a clear, accurate answer with source citations using [Source N] notation. "
        f"If the answer is not fully covered in the context, say so explicitly."
    )

    # Generate answer
    try:
        response = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        answer = response.content[0].text.strip()
    except Exception as exc:
        logger.error(f"Claude answer generation failed: {exc}")
        return {
            "success": False,
            "question": question,
            "answer": "Answer generation failed. Please try again.",
            "citations": [],
            "sources_used": 0,
            "error": str(exc),
        }

    citations = [
        {
            "source_number": i + 1,
            "document": doc.get("source", "Unknown"),
            "doc_type": doc.get("doc_type", "general"),
            "relevance_score": round(float(doc.get("score", 0)), 4),
        }
        for i, doc in enumerate(docs)
    ]

    duration_ms = int((datetime.utcnow() - started_at).total_seconds() * 1000)

    logger.info(
        f"District docs query | tenant={tenant_id} role={user_role} "
        f"sources={len(docs)} ms={duration_ms}"
    )

    return {
        "success": True,
        "question": question,
        "answer": answer,
        "citations": citations,
        "sources_used": len(docs),
        "doc_category_filter": doc_category,
        "role": user_role,
        "duration_ms": duration_ms,
    }