import logging
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware

from polragion.api.health import router as health_router
from polragion.api.work_items import router as work_item_router
from polragion.api.github_auth import router as auth_router
from polragion.application import copilot_service
from polragion.application.work_item_mapper import WorkItemIndexMapper
from polragion.application.work_item_service import WorkItemService
from polragion.domain.data_fetcher import DataFetcher
from polragion.domain.data_worker import DataWorker
from polragion.domain.vector_store import VectorStore
from polragion.infrastructure.errors import VectorStoreUnavailableError
from polragion.infrastructure.json_data_fetcher import JsonDataFetcher
from polragion.infrastructure.qdrant_data_worker import QdrantDataWorker
from polragion.infrastructure.qdrant_hybrid_vector_store import QdrantHybridVectorStore
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

        ai_service = copilot_service.CopilotService(app_settings)
        await ai_service.initialize()

        try:
            yield
        finally:
            vector_store.close()
            await ai_service.shutdown()

    app = FastAPI(
        title=app_settings.app_name,
        version="0.2.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        SessionMiddleware,
        secret_key=app_settings.github_session_secret,
        same_site="lax",
        https_only=False,
    )

    app.include_router(health_router)
    app.include_router(work_item_router)
    app.include_router(auth_router)

    @app.exception_handler(VectorStoreUnavailableError)
    async def handle_vector_store_unavailable(
        request: Request,
        exc: VectorStoreUnavailableError,
    ) -> JSONResponse:
        logger.warning(
            "Vector store unavailable during %s %s: %s",
            request.method,
            request.url.path,
            exc,
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": "Vector store is temporarily unavailable"},
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        logger.error(
            "Unhandled error during %s %s",
            request.method,
            request.url.path,
            exc_info=(type(exc), exc, exc.__traceback__),
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )

    return app


# Creating the ASGI object has no network side effects. Qdrant is initialized
# only when FastAPI enters its lifespan during application startup.
app = create_app()