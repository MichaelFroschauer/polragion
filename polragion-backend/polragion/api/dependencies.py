from fastapi import Request

from polragion.application.session_service import SessionService
from polragion.application.work_item_service import WorkItemService
from polragion.database.repository import UserRepository, GitHubCredentialsRepository
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


def get_user_repository(request: Request) -> UserRepository:
    return request.app.state.user_repository


def get_github_credentials_repository(request: Request) -> GitHubCredentialsRepository:
    return request.app.state.github_credentials_repository


def get_session_service(request: Request) -> SessionService:
    return request.app.state.session_service
