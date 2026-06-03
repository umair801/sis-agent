from langchain_openai import OpenAIEmbeddings
from app.core.config import settings


def get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=settings.OPENAI_API_KEY,
    )
