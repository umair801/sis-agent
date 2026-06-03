from app.rag.vector_store import similarity_search
from app.services.claude_service import call_claude
from app.core.logging import logger
import json


async def rag_query(
    query: str,
    tenant_id: str,
    role: str,
    k: int = 5,
) -> dict:
    # Retrieve relevant chunks
    docs = await similarity_search(query, tenant_id=tenant_id, k=k)

    if not docs:
        return {
            "answer": "No relevant documents found in the knowledge base for this query.",
            "citations": [],
            "sources_used": 0,
        }

    # Build context from retrieved docs
    context_parts = []
    for i, doc in enumerate(docs, 1):
        context_parts.append(
            f"[Source {i}: {doc['source']}, Page {doc['page']}]\n{doc['content']}"
        )
    context = "\n\n".join(context_parts)

    system = f"""You are a knowledgeable assistant for Datawebify Student Information System.
Answer questions based ONLY on the provided document context.
Always cite your sources using [Source N] notation.
If the answer is not in the context, say so clearly.
User role: {role}"""

    prompt = f"""Question: {query}

Document Context:
{context}

Provide a clear, accurate answer with source citations."""

    try:
        answer = await call_claude(prompt, system=system, max_tokens=1024)

        citations = [
            {
                "source": doc["source"],
                "page": doc["page"],
                "relevance_score": doc["score"],
                "doc_type": doc["doc_type"],
            }
            for doc in docs
        ]

        return {
            "answer": answer,
            "citations": citations,
            "sources_used": len(docs),
        }

    except Exception as e:
        logger.error("RAG query failed", error=str(e))
        return {
            "answer": f"Error generating answer: {str(e)}",
            "citations": [],
            "sources_used": 0,
        }
