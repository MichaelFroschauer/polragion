from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from polragion.api.dependencies import get_vector_store
from polragion.api.schemas import HealthResponse
from polragion.domain.vector_store import VectorStore

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live", response_model=HealthResponse)
def liveness() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/ready", response_model=HealthResponse)
def readiness(
    vector_store: Annotated[VectorStore, Depends(get_vector_store)],
) -> HealthResponse:
    if not vector_store.is_ready():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vector store is not ready",
        )
    return HealthResponse(status="ok")
