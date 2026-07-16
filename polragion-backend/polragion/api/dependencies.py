from fastapi import Request

from polragion.application.work_item_service import WorkItemService
from polragion.domain.vector_store import VectorStore
from polragion.settings import Settings


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_vector_store(request: Request) -> VectorStore:
    return request.app.state.vector_store


def get_work_item_service(request: Request) -> WorkItemService:
    return request.app.state.work_item_service
