from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from app.rag.ingestion import ingest_document
from app.rag.retriever import rag_query
from app.core.dependencies import get_current_user, require_roles
from app.schemas.auth import TokenPayload

router = APIRouter(prefix="/rag", tags=["RAG"])


class RAGQueryRequest(BaseModel):
    query: str
    k: int = 5


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = Form(default="policy"),
    current_user: TokenPayload = Depends(require_roles(
        "SuperAdmin", "DistrictAdmin", "Principal", "SpEdCoordinator"
    )),
):
    allowed = ["application/pdf", "text/plain"]
    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported")

    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size must be under 10MB")

    contents = await file.read()
    result = await ingest_document(
        file_bytes=contents,
        filename=file.filename,
        tenant_id=current_user.tenant_id,
        doc_type=doc_type,
        uploaded_by=current_user.sub,
    )

    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])

    return result


@router.post("/query")
async def query_documents(
    payload: RAGQueryRequest,
    current_user: TokenPayload = Depends(get_current_user),
):
    result = await rag_query(
        query=payload.query,
        tenant_id=current_user.tenant_id,
        role=current_user.role,
        k=payload.k,
    )
    return result
