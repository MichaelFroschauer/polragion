import uuid

_POINT_NAMESPACE = uuid.UUID("8604873a-0779-49ef-81c4-840c4567d718")
_DOCUMENT_ID_PAYLOAD_KEY = "_polragion_document_id"
_INDEX_MODEL_PAYLOAD_KEY = "_polragion_embedding_model"
_INDEX_SCHEMA_PAYLOAD_KEY = "_polragion_schema_version"
_RESERVED_PAYLOAD_KEYS = {
    _DOCUMENT_ID_PAYLOAD_KEY,
    _INDEX_MODEL_PAYLOAD_KEY,
    _INDEX_SCHEMA_PAYLOAD_KEY,
}

def qdrant_point_id(logical_id: str) -> str:
    """Create a deterministic UUID accepted by Qdrant."""

    return str(uuid.uuid5(_POINT_NAMESPACE, logical_id))
