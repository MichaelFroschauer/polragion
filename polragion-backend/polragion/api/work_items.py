import logging
from time import perf_counter
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from polragion.api.dependencies import get_settings, get_work_item_service
from polragion.api.schemas import IngestResponse, WorkItemSearchHitResponse
from polragion.application.work_item_service import WorkItemService
from polragion.domain.work_item import PolarionWorkItem
from polragion.settings import Settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/work-items", tags=["work-items"])


@router.post(
    "",
    response_model=IngestResponse,
    status_code=status.HTTP_200_OK,
)
def ingest_work_items(
    data: Annotated[
        list[PolarionWorkItem],
        Body(min_length=1, max_length=50_000),
    ],
    service: Annotated[WorkItemService, Depends(get_work_item_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> IngestResponse:
    if len(data) > settings.max_ingest_batch_size:
        # The OpenAPI-level maximum is deliberately conservative. This runtime
        # check allows deployments to configure an even smaller limit.
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"At most {settings.max_ingest_batch_size} work items may be ingested per request."
            ),
        )

    started_at = perf_counter()
    count = service.ingest(data)
    logger.info(
        "Ingested %d work items in %.3f seconds",
        count,
        perf_counter() - started_at,
    )
    return IngestResponse(status="ok", ingested_items=count)


@router.get(
    "/search",
    response_model=list[WorkItemSearchHitResponse],
)
def search_work_items(
    prompt: Annotated[str, Query(min_length=1, max_length=10_000)],
    service: Annotated[WorkItemService, Depends(get_work_item_service)],
    settings: Annotated[Settings, Depends(get_settings)],
    project_id: Annotated[str | None, Query(min_length=1, max_length=128)] = None,
    limit: Annotated[int | None, Query(ge=1)] = None,
    score_threshold: Annotated[float | None, Query(ge=0.0, le=1.0)] = None,
) -> list[WorkItemSearchHitResponse]:
    effective_limit = limit or settings.search_default_limit
    if effective_limit > settings.search_max_limit:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"limit must not exceed {settings.search_max_limit}",
        )

    effective_threshold = (
        score_threshold if score_threshold is not None else settings.search_score_threshold
    )

    started_at = perf_counter()
    results = service.search(
        prompt,
        limit=effective_limit,
        project_id=project_id,
        score_threshold=effective_threshold,
    )
    logger.info(
        "Work-item search returned %d results in %.3f seconds",
        len(results),
        perf_counter() - started_at,
    )

    return [
        WorkItemSearchHitResponse(
            work_item=result.work_item,
            score=result.score,
            point_id=result.point_id,
        )
        for result in results
    ]
