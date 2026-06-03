from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
from app.rag.embeddings import get_embeddings
from app.core.config import settings
from app.core.logging import logger


def get_vector_store(namespace: str = None) -> PineconeVectorStore:
    pc = Pinecone(api_key=settings.PINECONE_API_KEY)
    index = pc.Index(settings.PINECONE_INDEX_NAME)
    ns = namespace or settings.PINECONE_NAMESPACE

    return PineconeVectorStore(
        index=index,
        embedding=get_embeddings(),
        namespace=ns,
    )


async def similarity_search(
    query: str,
    tenant_id: str,
    k: int = 5,
    namespace: str = None,
) -> list[dict]:
    try:
        ns = namespace or f"sis-{tenant_id[:8]}"
        store = get_vector_store(namespace=ns)
        docs = store.similarity_search_with_score(query, k=k)

        results = []
        for doc, score in docs:
            results.append({
                "content": doc.page_content,
                "source": doc.metadata.get("source", "Unknown"),
                "page": doc.metadata.get("page", 0),
                "score": round(float(score), 4),
                "doc_type": doc.metadata.get("doc_type", "general"),
            })
        return results
    except Exception as e:
        logger.error("Vector search failed", error=str(e))
        return []
