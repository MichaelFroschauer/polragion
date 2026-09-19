import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from polragion.api.dependencies import get_settings, get_polarion_descriptor
from polragion.api.models import PolarionMetadataResponse, PolarionProjectMetadata, PolarionDocumentMetadata
from polragion.domain.polarion_descriptor import PolarionDescriptor
from polragion.infrastructure.errors import ConfigurationError
from polragion.models.polarion_config import PolarionImportConfig, load_import_config
from polragion.settings import Settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/polarion-metadata", tags=["polarion-metadata"])


@router.post(
    "/load-config",
    status_code=status.HTTP_200_OK,
)
def load_polarion_import_config(
    settings: Annotated[Settings, Depends(get_settings)],
    polarion_descriptor: Annotated[PolarionDescriptor, Depends(get_polarion_descriptor)],
) -> PolarionImportConfig:

    # TODO: Maybe change this so that there exists an ingested version of the polarion import config file which is updated if a new ingest happens
    try:
        polarion_descriptor.update_data()
        return load_import_config(settings.polarion_import_config_path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={ "message": str(exc), "errors": exc.errors },
        ) from exc


@router.get(
    "/get-config",
    status_code=status.HTTP_200_OK,
)
def get_polarion_import_config(
    settings: Annotated[Settings, Depends(get_settings)],
) -> PolarionImportConfig:

    try:
        return load_import_config(settings.polarion_import_config_path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={ "message": str(exc), "errors": exc.errors },
        ) from exc


@router.get(
    "/get-search-scopes",
    status_code=status.HTTP_200_OK,
)
def get_polarion_search_scopes(
    polarion_descriptor: Annotated[PolarionDescriptor, Depends(get_polarion_descriptor)],
) -> PolarionMetadataResponse:

    try:
        project_ids = polarion_descriptor.get_project_ids()
        return PolarionMetadataResponse(
            project_ids=project_ids,
            project_categories=polarion_descriptor.get_project_categories(),
            project_contexts=polarion_descriptor.get_project_contexts(),
            projects=[
                PolarionProjectMetadata(
                    id=project_id,
                    contexts=polarion_descriptor.get_project_context(project_id),
                    documents=[
                        PolarionDocumentMetadata(
                            name=document_name,
                            category=polarion_descriptor.get_document_category(project_id, document_name) or "",
                        )
                        for document_name in polarion_descriptor.get_documents(project_id)
                    ]
                )
                for project_id in project_ids
            ]
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={ "message": str(exc), "errors": exc.errors },
        ) from exc
