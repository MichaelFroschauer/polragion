from fastapi import FastAPI
from fastapi.testclient import TestClient

from polragion.api.auth import get_current_user
from polragion.api.dependencies import get_settings, get_vector_store, get_work_item_service
from polragion.api.health import router as health_router
from polragion.api.work_items import router as work_item_router
from polragion.application.work_item_mapper import WorkItemIndexMapper
from polragion.application.work_item_service import WorkItemService
from polragion.domain.vector_store import VectorSearchHit
from polragion.models.user import User
from polragion.settings import Settings
from tests.factories import make_work_item
from tests.fakes import FakeVectorStore


def make_test_app(store: FakeVectorStore) -> FastAPI:
    app = FastAPI()
    app.include_router(work_item_router)
    app.include_router(health_router)
    service = WorkItemService(store, WorkItemIndexMapper())
    app.dependency_overrides[get_current_user] = lambda: User(
        github_user_id="1", username="test", name="", avatar_url=""
    )
    app.dependency_overrides[get_settings] = lambda: Settings(max_ingest_batch_size=10)
    app.dependency_overrides[get_work_item_service] = lambda: service
    app.dependency_overrides[get_vector_store] = lambda: store
    return app


def test_ingest_and_search_routes() -> None:
    fake_store = FakeVectorStore()
    item = make_work_item()
    fake_store.search_results = [
        VectorSearchHit(
            document_id="DEMO:REQ-123",
            point_id="point-1",
            score=0.91,
            reranker_score=None,
            metadata=item.model_dump(mode="json"),
        )
    ]
    with TestClient(make_test_app(fake_store)) as client:
        ingest_response = client.post(
            "/v1/work-items/ingest",
            json=[item.model_dump(mode="json")],
        )
        search_response = client.post(
            "/v1/work-items/search",
            json={"prompt": "authentication", "filters": {"project_ids": ["DEMO"]}},
        )

    assert ingest_response.status_code == 200
    assert ingest_response.json() == {"status": "ok", "ingested_items": 1}
    assert search_response.status_code == 200
    assert search_response.json()["work_items"][0]["score"] == 0.91
    assert fake_store.last_search["db_filters"][0].key == "project_id"
    assert fake_store.last_search["db_filters"][0].value == ["DEMO"]


def test_readiness_returns_503_when_store_is_not_ready() -> None:
    fake_store = FakeVectorStore()
    fake_store.ready = False
    with TestClient(make_test_app(fake_store)) as client:
        response = client.get("/health/ready")
    assert response.status_code == 503
