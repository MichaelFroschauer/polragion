import logging
from pathlib import Path
from time import perf_counter
from typing import Annotated, Iterable

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status, Request

from polragion.api.auth import get_current_user
from polragion.api.dependencies import get_settings, get_work_item_service, get_data_fetcher, get_data_worker, \
    get_ai_service
from polragion.api.models import IngestResponse, WorkItemAskResponse, WorkItemSearchResponse
from polragion.application.ai_service import AiService, ChatHistoryMessage
from polragion.application.work_item_service import WorkItemService
from polragion.domain.data_fetcher import DataFetcher
from polragion.domain.data_worker import DataWorker
from polragion.infrastructure.polarion_data_fetcher import PolarionDataFetcher
from polragion.application.prompt_builder import AnswerDetail, get_prompt_message, get_prompt_message_with_work_items
from polragion.models.ai_message import CopilotResponseMessage, CopilotSendMessage
from polragion.models.polarion_config import load_import_config, PolarionImportConfig
from polragion.models.user import User
from polragion.models.work_item import PolarionWorkItem, WorkItemSearchHit
from polragion.settings import Settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/work-items", tags=["work-items"])


@router.post(
    "/load-config",
    status_code=status.HTTP_200_OK,
)
def load_polarion_import_config(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
) -> PolarionImportConfig:

    # TODO: Maybe change this so that there exists an ingested version of the polarion import config file which is updated if a new ingest happens
    polarion_config: PolarionImportConfig = load_import_config(settings.polarion_import_config_path)
    request.app.state.polarion_config = polarion_config

    return polarion_config


@router.get(
    "/get-config",
    status_code=status.HTTP_200_OK,
)
def get_import_config(
    request: Request,
) -> PolarionImportConfig:

    return request.app.state.polarion_config


@router.post(
    "/ingest",
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


@router.post(
    "/ingest/import-json",
    response_model=IngestResponse,
    status_code=status.HTTP_200_OK,
)
def ingest_work_items_from_json_data_source(
    data_fetcher: Annotated[DataFetcher, Depends(get_data_fetcher)],
    data_worker: Annotated[DataWorker, Depends(get_data_worker)],
    limit: Annotated[int | None, Query(ge=1)] = None,
) -> IngestResponse:

    count = data_worker.work(data_fetcher.fetch_data(limit))
    return IngestResponse(status="ok", ingested_items=count)



@router.post(
    "/ingest/import-polarion",
    response_model=IngestResponse,
    status_code=status.HTTP_200_OK,
)
def ingest_work_items_from_polarion_data_source(
    settings: Annotated[Settings, Depends(get_settings)],
    data_worker: Annotated[DataWorker, Depends(get_data_worker)],
    limit: Annotated[int | None, Query(ge=1)] = None,
) -> IngestResponse:

    config = load_import_config(Path(settings.polarion_import_config_path))

    data_fetcher = PolarionDataFetcher(settings, config)
    data: Iterable[PolarionWorkItem] = data_fetcher.fetch_data(limit)
    count = data_worker.work(data)

    return IngestResponse(status="ok", ingested_items=count)


@router.get(
    "/search",
    response_model=WorkItemSearchResponse,
)
def search_work_items(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    prompt: Annotated[str, Query(min_length=1, max_length=10_000)],
    work_item_service: Annotated[WorkItemService, Depends(get_work_item_service)],
    project_id: Annotated[str | None, Query(min_length=1, max_length=128)] = None,
    limit: Annotated[int | None, Query(ge=1)] = None,
    score_threshold: Annotated[float | None, Query(ge=0.0, le=1.0)] = None,
    do_reranking: bool | None = None,
) -> WorkItemSearchResponse:

    effective_limit = limit or settings.search_default_limit
    if effective_limit > settings.search_max_limit:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"limit must not exceed {settings.search_max_limit}",
        )

    effective_threshold = score_threshold if score_threshold is not None else settings.search_score_threshold

    started_at = perf_counter()
    results: list[WorkItemSearchHit] = work_item_service.search(
        prompt,
        limit=effective_limit,
        project_id=project_id,
        score_threshold=effective_threshold,
        do_reranking=do_reranking,
    )
    logger.info(
        "Work-item search returned %d results in %.3f seconds",
        len(results),
        perf_counter() - started_at,
    )

    work_item_search_hits = [
        WorkItemSearchHit(
            work_item=result.work_item,
            score=result.score,
            point_id=result.point_id,
        )
        for result in results
    ]

    return WorkItemSearchResponse(work_items=work_item_search_hits)


@router.post(
    "/ask-with-search",
    response_model=WorkItemAskResponse,
    status_code=status.HTTP_200_OK,
    response_model_by_alias=True,
)
async def ask_work_item_with_initial_search(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
    prompt: Annotated[str, Query(min_length=1, max_length=10_000)],
    work_item_service: Annotated[WorkItemService, Depends(get_work_item_service)],
    ai_service: Annotated[AiService, Depends(get_ai_service)],
    project_id: Annotated[str | None, Query(min_length=1, max_length=128)] = None,
    limit_work_item_search: Annotated[int | None, Query(ge=1)] = None,
    limit_ai_model_work_items: Annotated[int | None, Query(ge=1)] = None,
    score_threshold: Annotated[float | None, Query(ge=0.0, le=1.0)] = None,
    do_reranking: bool | None = None,
    user_defined_system_prompt: str | None = None,
    answer_detail: Annotated[AnswerDetail, Query()] = AnswerDetail.AUTO,
) -> WorkItemAskResponse:

    hits: WorkItemSearchResponse = search_work_items(
        request=request,
        settings=settings,
        prompt=prompt,
        work_item_service=work_item_service,
        project_id=project_id,
        limit=limit_work_item_search,
        score_threshold=score_threshold,
        do_reranking=do_reranking,
    )

    work_items = hits.work_items[:limit_ai_model_work_items]
    ai_prompt = get_prompt_message_with_work_items(
        user_prompt=prompt,
        user_system_prompt=user_defined_system_prompt,
        answer_detail=answer_detail,
        work_items=work_items,
    )

    response: CopilotResponseMessage = await ai_service.send_message(
        CopilotSendMessage(
            user_id=current_user.id,
            text=ai_prompt,
            display_text=prompt,
        )
    )

    # Combine the initially searched hits with any the AI fetched via tools.
    seen_point_ids = {hit.point_id for hit in hits.work_items}
    combined_work_items = list(hits.work_items)
    work_items_of_context = response.request_context.collected_work_items() if response.request_context else []
    for hit in work_items_of_context:
        if hit.point_id not in seen_point_ids:
            seen_point_ids.add(hit.point_id)
            combined_work_items.append(hit)

    return WorkItemAskResponse(answer=response.text, tokens_spent=0, work_items=combined_work_items)


@router.post(
    "/ask",
    response_model=WorkItemAskResponse,
    status_code=status.HTTP_200_OK,
    response_model_by_alias=True,
)
async def ask_work_item(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
    prompt: Annotated[str, Query(min_length=1, max_length=10_000)],
    work_item_service: Annotated[WorkItemService, Depends(get_work_item_service)],
    ai_service: Annotated[AiService, Depends(get_ai_service)],
    project_id: Annotated[str | None, Query(min_length=1, max_length=128)] = None,
    limit_work_item_search: Annotated[int | None, Query(ge=1)] = None,
    limit_ai_model_work_items: Annotated[int | None, Query(ge=1)] = None,
    score_threshold: Annotated[float | None, Query(ge=0.0, le=1.0)] = None,
    do_reranking: bool | None = None,
    user_defined_system_prompt: str | None = None,
    answer_detail: Annotated[AnswerDetail, Query()] = AnswerDetail.AUTO,
) -> WorkItemAskResponse:

    ai_prompt = get_prompt_message(user_prompt=prompt, user_system_prompt=user_defined_system_prompt, answer_detail=answer_detail)

    response: CopilotResponseMessage = await ai_service.send_message(
        CopilotSendMessage(
            user_id=current_user.id,
            text=ai_prompt,
            display_text=prompt,
        )
    )

    work_items = response.request_context.collected_work_items() if response.request_context else []
    return WorkItemAskResponse(answer=response.text, tokens_spent=0, work_items=work_items)


@router.get(
    "/ask/history",
    response_model=list[ChatHistoryMessage],
    status_code=status.HTTP_200_OK,
)
async def get_chat_history(
    current_user: Annotated[User, Depends(get_current_user)],
    ai_service: Annotated[AiService, Depends(get_ai_service)],
) -> list[ChatHistoryMessage]:
    return await ai_service.get_chat_history(current_user.id)


@router.get(
    "/reset",
    status_code=status.HTTP_200_OK,
)
async def reset_user_session(
    current_user: Annotated[User, Depends(get_current_user)],
    ai_service: Annotated[AiService, Depends(get_ai_service)],
) -> None:
    await ai_service.close_user_session(current_user.id)
