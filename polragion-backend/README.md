# Polragion Backend

A small FastAPI backend for indexing Polarion work items in Qdrant and searching them semantically.

## Architecture

```text
HTTP API
  -> WorkItemService
      -> WorkItemIndexMapper
      -> VectorStore protocol
          -> QdrantVectorStore adapter
```

The domain model does not import Qdrant. Qdrant is initialized during the FastAPI lifespan, not during module import. Tests inject an in-memory fake through the same `VectorStore` protocol.

## Requirements

- Python 3.12 or newer
- A running Qdrant instance
- `uv` is recommended, but standard `pip` also works

## Setup with uv

```bash
cp .env.example .env
uv sync --extra dev
uv run uvicorn polragion.app:app --reload
```

The legacy command remains valid:

```bash
uv run uvicorn vector_store.main:app --reload
```

## Tests

```bash
uv run pytest
```

The unit and API tests do not require Qdrant.

## Endpoints

- `GET /health/live`
- `GET /health/ready`
- `POST /v1/work-items`
- `GET /v1/work-items/search`

See `test_main.http` for complete request examples.

## Collection versioning

The Qdrant collection name is derived from:

- `QDRANT_COLLECTION_PREFIX`
- `FASTEMBED_DENSE_MODEL`
- `FASTEMBED_SPARSE_MODEL`
- `INDEX_SCHEMA_VERSION`

This prevents vectors produced by different embedding models or schema versions from being mixed. Increment `INDEX_SCHEMA_VERSION` whenever the embedding text strategy changes incompatibly.

## Project-scoped IDs

A document's logical ID is `project_id:workitem_id`. This avoids collisions when different Polarion projects use the same work-item identifier. Search can be restricted with the `project_id` query parameter.

## Why no Celery yet?

The current synchronous Qdrant client is used from synchronous FastAPI routes, which FastAPI executes in a worker thread. A task queue should be introduced only when ingestion jobs become long-running, need retries independent of the HTTP request, or must survive API restarts.
