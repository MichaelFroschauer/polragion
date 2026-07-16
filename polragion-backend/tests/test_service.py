from polragion.application.work_item_mapper import WorkItemIndexMapper
from polragion.application.work_item_service import WorkItemService
from polragion.domain.vector_store import VectorSearchHit
from tests.factories import make_work_item
from tests.fakes import FakeVectorStore


def test_service_ingests_without_qdrant() -> None:
    store = FakeVectorStore()
    service = WorkItemService(store, WorkItemIndexMapper())

    count = service.ingest([make_work_item()])

    assert count == 1
    assert len(store.documents) == 1
    assert store.documents[0].id == "DEMO:REQ-123"


def test_service_reconstructs_typed_search_result() -> None:
    item = make_work_item()
    store = FakeVectorStore()
    store.search_results = [
        VectorSearchHit(
            document_id="DEMO:REQ-123",
            point_id="point-1",
            score=0.91,
            metadata=item.model_dump(mode="json"),
        )
    ]
    service = WorkItemService(store, WorkItemIndexMapper())

    results = service.search("authentication", limit=5, project_id="DEMO")

    assert results[0].work_item == item
    assert results[0].score == 0.91
    assert results[0].point_id == "point-1"
