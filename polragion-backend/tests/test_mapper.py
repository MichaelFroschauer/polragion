from polragion.application.work_item_mapper import WorkItemIndexMapper
from tests.factories import make_work_item


def test_work_item_is_mapped_to_vector_document() -> None:
    item = make_work_item()

    document = WorkItemIndexMapper().to_document(item)

    assert document.id == "DEMO:REQ-123"
    assert "The system shall authenticate users" in document.text
    assert document.metadata["project_id"] == "DEMO"
    assert document.metadata["workitem_id"] == "REQ-123"
