from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_knowledge_service
from app.core.response import ResponseEnvelope, success_response
from app.schemas.knowledge import KnowledgeQueryRequest, KnowledgeQueryResult
from app.services.knowledge_service import KnowledgeService

router = APIRouter()


@router.post("/query", response_model=ResponseEnvelope[KnowledgeQueryResult])
def query_knowledge_base(
    payload: KnowledgeQueryRequest,
    service: KnowledgeService = Depends(get_knowledge_service),
) -> ResponseEnvelope[KnowledgeQueryResult]:
    return success_response(service.query(payload.query, top_k=payload.top_k))
