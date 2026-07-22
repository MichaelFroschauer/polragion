import logging
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from datetime import timedelta

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from polragion.api.health import router as health_router
from polragion.api.work_items import router as work_item_router
from polragion.api.auth import router as auth_router
from polragion.application.ai_service import AiMessageEventT
from polragion.application.session_service import SessionService
from polragion.application.work_item_mapper import WorkItemIndexMapper
from polragion.application.work_item_service import WorkItemService
from polragion.database.memory_repository import InMemorySessionRepository, InMemoryUserRepository, \
    InMemoryGitHubCredentialsRepository
from polragion.domain.data_fetcher import DataFetcher
from polragion.domain.data_worker import DataWorker
from polragion.domain.vector_store import VectorStore
from polragion.infrastructure.copilot_service import CopilotService
from polragion.infrastructure.json_data_fetcher import JsonDataFetcher
from polragion.infrastructure.qdrant_data_worker import QdrantDataWorker
from polragion.infrastructure.qdrant_vector_store import QdrantVectorStore
from polragion.settings import Settings

logger = logging.getLogger(__name__)
VectorStoreFactory = Callable[[Settings], VectorStore]
DataFetcherFactory = Callable[[Settings], DataFetcher]
DataWorkerFactory = Callable[[Settings, WorkItemService], DataWorker]


def _configure_logging(settings: Settings) -> None:
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def create_app(
    *,
    settings: Settings | None = None,
    vector_store_factory: VectorStoreFactory = QdrantVectorStore,
    data_fetcher_factory: DataFetcherFactory = JsonDataFetcher,
    data_worker_factory: DataWorkerFactory = QdrantDataWorker,
) -> FastAPI:
    app_settings = settings or Settings()
    _configure_logging(app_settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        vector_store = vector_store_factory(app_settings)
        vector_store.initialize()

        app.state.settings = app_settings
        app.state.vector_store = vector_store
        app.state.work_item_service = WorkItemService(
            vector_store=vector_store,
            mapper=WorkItemIndexMapper(),
        )
        app.state.data_fetcher = data_fetcher_factory(app_settings)
        app.state.data_worker = data_worker_factory(app_settings, app.state.work_item_service)

        session_repository = InMemorySessionRepository()
        user_repository = InMemoryUserRepository()
        github_credentials_repository = InMemoryGitHubCredentialsRepository()

        app.state.session_repository = session_repository
        app.state.user_repository = user_repository
        app.state.github_credentials_repository = github_credentials_repository

        app.state.session_service = SessionService(session_repository, session_lifetime=timedelta(days=7))
        app.state.ai_service = CopilotService(app_settings, github_credentials_repository, runtime_url="localhost:4321")

        def ai_message_event(event: AiMessageEventT) -> None:
            print("****** NEW AI MESSAGE ******")
            print(f"user_id: {str(event.user_id)}")
            print(f"message: {event.message.text}")

        unsubscribe = app.state.ai_service.add_message_response_handler(ai_message_event)

        try:
            yield
        finally:
            vector_store.close()
            unsubscribe()

    app = FastAPI(
        title=app_settings.app_name,
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        SessionMiddleware,
        secret_key=app_settings.session_secret,
        session_cookie="polragion_session",
        max_age=7 * 24 * 60 * 60,
        same_site="lax",
        https_only=not app_settings.debug,
    )

    # origins = [
    #     "http://localhost",
    #     "http://localhost:8080",
    # ]
    # app.add_middleware(
    #     CORSMiddleware,
    #     allow_origins=origins,
    #     allow_credentials=True,
    #     allow_methods=["*"],
    #     allow_headers=["*"],
    # )

    app.include_router(health_router)
    app.include_router(work_item_router)
    app.include_router(auth_router)

    return app


# Creating the ASGI object has no network side effects. Qdrant is initialized
# only when FastAPI enters its lifespan during application startup.
app = create_app()
