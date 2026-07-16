from fastapi import Request

from polragion.application.work_item_service import WorkItemService
from polragion.domain.data_fetcher import DataFetcher
from polragion.domain.data_worker import DataWorker
from polragion.domain.vector_store import VectorStore
from polragion.settings import Settings


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_vector_store(request: Request) -> VectorStore:
    return request.app.state.vector_store


def get_work_item_service(request: Request) -> WorkItemService:
    return request.app.state.work_item_service

def get_data_fetcher(request: Request) -> DataFetcher:
    return request.app.state.data_fetcher

def get_data_worker(request: Request) -> DataWorker:
    return request.app.state.data_worker