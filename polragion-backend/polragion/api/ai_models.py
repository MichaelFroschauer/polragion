from pydantic import BaseModel, ConfigDict, Field

import logging
from datetime import timedelta, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends

from starlette import status

from polragion.api.auth import get_current_user
from polragion.api.dependencies import get_settings, get_github_credentials_repository, get_ai_service
from polragion.api.github_api_utils import get_github_available_models
from polragion.application.ai_service import AiService
from polragion.database.repository import GitHubCredentialsRepository
from polragion.models.user import User
from polragion.settings import Settings
from polragion.utils.general import utc_now

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/github", tags=["GitHub Models"])


class GitHubAiModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    publisher: str
    registry: str | None = None
    summary: str | None = None
    html_url: str | None = None
    version: str | None = None
    rate_limit_tier: str

    capabilities: list[str] = Field(default_factory=list)
    supported_input_modalities: list[str] = Field(default_factory=list)
    supported_output_modalities: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    # max_input_tokens: int
    # max_output_tokens: int


class UserGitHubModels(BaseModel):
    user_id: UUID
    models: list[GitHubAiModel]
    last_refresh: datetime


user_models: dict[UUID, UserGitHubModels] = {}


@router.get(
    "/models",
    status_code=status.HTTP_200_OK,
)
async def get_user_models(
        current_user: Annotated[User, Depends(get_current_user)],
        settings: Annotated[Settings, Depends(get_settings)],
        credentials_repository: Annotated[GitHubCredentialsRepository, Depends(get_github_credentials_repository)],
) -> list[GitHubAiModel]:
    user_model = user_models.get(current_user.id)
    if (user_model is not None and user_model.last_refresh is not None
            and user_model.last_refresh > utc_now() + timedelta(hours=24)):
        return user_model.models

    credentials = await credentials_repository.get_by_id(current_user.id)
    if credentials is None:
        return []

    github_models: list[dict] = await get_github_available_models(settings, credentials)
    models = [GitHubAiModel.model_validate(model) for model in github_models]

    user_models[current_user.id] = UserGitHubModels(user_id=current_user.id, models=models, last_refresh=utc_now())

    return models


@router.get(
    "/model",
    response_model=GitHubAiModel,
    status_code=status.HTTP_200_OK,
)
async def get_model(
        current_user: Annotated[User, Depends(get_current_user)],
        settings: Annotated[Settings, Depends(get_settings)],
        credentials_repository: Annotated[GitHubCredentialsRepository, Depends(get_github_credentials_repository)],
        ai_service: Annotated[AiService, Depends(get_ai_service)],
):
    available_models = await get_user_models(current_user, settings, credentials_repository)
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

    return current_model


@router.put(
    "/model",
    response_model=GitHubAiModel,
    status_code=status.HTTP_200_OK,
)
async def set_user_model(
        current_user: Annotated[User, Depends(get_current_user)],
        settings: Annotated[Settings, Depends(get_settings)],
        credentials_repository: Annotated[GitHubCredentialsRepository, Depends(get_github_credentials_repository)],
        ai_service: Annotated[AiService, Depends(get_ai_service)],
        model_id: str,
) -> GitHubAiModel:
    available_models: list[GitHubAiModel] = await get_user_models(current_user, settings, credentials_repository)
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

    await ai_service.set_model_for_session(current_user.id, model_id)

    return selected_model
