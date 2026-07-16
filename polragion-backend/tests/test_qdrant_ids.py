from polragion.infrastructure.qdrant_vector_store import qdrant_point_id


def test_qdrant_point_id_is_deterministic() -> None:
    assert qdrant_point_id("DEMO:REQ-123") == qdrant_point_id("DEMO:REQ-123")


def test_project_is_part_of_identity() -> None:
    assert qdrant_point_id("A:REQ-123") != qdrant_point_id("B:REQ-123")
