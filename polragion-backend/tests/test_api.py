from fastapi.testclient import TestClient

from polragion.app import create_app
from polragion.domain.vector_store import VectorSearchHit
from polragion.settings import Settings
from tests.factories import make_work_item
from tests.fakes import FakeVectorStore


def test_ingest_and_search_routes() -> None:
    fake_store = FakeVectorStore()
    item = make_work_item()
    fake_store.search_results = [
        VectorSearchHit(
            document_id="DEMO:REQ-123",
            point_id="point-1",
            score=0.91,
            metadata=item.model_dump(mode="json"),
        )
    ]
    app = create_app(
        settings=Settings(max_ingest_batch_size=10),
        vector_store_factory=lambda _settings: fake_store,
    )

    with TestClient(app) as client:
        ingest_response = client.post(
            "/v1/work-items",
            json=[item.model_dump(mode="json")],
        )
        search_response = client.get(
            "/v1/work-items/search",
            params={"prompt": "authentication", "project_id": "DEMO"},
        )

    assert ingest_response.status_code == 200
    assert ingest_response.json() == {"status": "ok", "ingested_items": 1}
    assert search_response.status_code == 200
    assert search_response.json()[0]["score"] == 0.91
    assert fake_store.initialized is True
    assert fake_store.closed is True


def test_readiness_returns_503_when_store_is_not_ready() -> None:
    fake_store = FakeVectorStore()
    fake_store.ready = False
    app = create_app(vector_store_factory=lambda _settings: fake_store)

    with TestClient(app) as client:
        response = client.get("/health/ready")

    assert response.status_code == 503
