from pydantic import BaseModel, ConfigDict

import logging
from datetime import timedelta, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends

from starlette import status

from polragion.api.auth import get_current_user
from polragion.api.dependencies import get_settings, get_ai_service
from polragion.application.ai_service import AiService
from polragion.models.ai_message import CopilotModel
from polragion.models.user import User
from polragion.settings import Settings
from polragion.utils.general import utc_now

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai/github", tags=["GitHub Models"])


class UserGitHubModels(BaseModel):
    user_id: UUID
    models: list[CopilotModel]
    last_refresh: datetime

user_models: dict[UUID, UserGitHubModels] = {}


class CopilotModelSelection(BaseModel):
    """The model a user has selected plus the reasoning effort applied to it."""

    model_config = ConfigDict(protected_namespaces=())

    model: CopilotModel
    reasoning_effort: str | None = None

def _resolve_reasoning_effort(model: CopilotModel, requested_effort: str | None) -> str | None:
    supported = model.supported_reasoning_efforts or []

    if not model.supports_reasoning_effort or not supported:
        if requested_effort is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Model {model.id} does not support a reasoning effort",
            )
        return None

    if requested_effort is None:
        return model.default_reasoning_effort

    if requested_effort not in supported:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Reasoning effort '{requested_effort}' is not supported by model {model.id}. "
                   f"Supported values: {', '.join(supported)}",
        )

    return requested_effort


@router.get(
    "/models",
    status_code=status.HTTP_200_OK,
)
async def get_user_models(
        current_user: Annotated[User, Depends(get_current_user)],
        settings: Annotated[Settings, Depends(get_settings)],
        ai_service: Annotated[AiService, Depends(get_ai_service)],
) -> list[CopilotModel]:

    user_model = user_models.get(current_user.id)

    if (
        user_model is not None
        and user_model.last_refresh is not None
        and utc_now() < user_model.last_refresh + timedelta(hours=24)
    ):
        return user_model.models

    github_models = await ai_service.get_available_models(current_user.id)

    models = [CopilotModel.model_validate(model) for model in github_models]
    user_models[current_user.id] = UserGitHubModels(user_id=current_user.id, models=models, last_refresh=utc_now())

    return models


@router.get(
    "/model",
    response_model=CopilotModelSelection,
    status_code=status.HTTP_200_OK,
)
async def get_model(
        current_user: Annotated[User, Depends(get_current_user)],
        settings: Annotated[Settings, Depends(get_settings)],
        ai_service: Annotated[AiService, Depends(get_ai_service)],
):
    available_models = await get_user_models(current_user, settings, ai_service)
    current_model_id = await ai_service.get_model_of_session(current_user.id)
    current_model = next(
        (
            model
            for model in available_models
            if model.id == current_model_id
        ),
        None,
    )

    if current_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Current model with ID {current_model_id} not found")

    current_reasoning_effort = await ai_service.get_reasoning_effort_of_session(current_user.id)

    return CopilotModelSelection(
        model=current_model,
        reasoning_effort=current_reasoning_effort,
    )


@router.put(
    "/model",
    response_model=CopilotModelSelection,
    status_code=status.HTTP_200_OK,
)
async def set_user_model(
        current_user: Annotated[User, Depends(get_current_user)],
        settings: Annotated[Settings, Depends(get_settings)],
        ai_service: Annotated[AiService, Depends(get_ai_service)],
        model_id: str,
        reasoning_effort: str | None = None,
) -> CopilotModelSelection:
    available_models: list[CopilotModel] = await get_user_models(current_user, settings, ai_service)
    selected_model = next(
        (
            model
            for model in available_models
            if model.id == model_id
        ),
        None,
    )

    if selected_model is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Model with ID {model_id} not found")

    effort = _resolve_reasoning_effort(selected_model, reasoning_effort)

    await ai_service.set_model_for_session(current_user.id, model_id, effort)

    return CopilotModelSelection(model=selected_model, reasoning_effort=effort)
