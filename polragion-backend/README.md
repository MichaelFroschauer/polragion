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

## GitHub access

Set `GITHUB_USER_CONFIG_PATH` to a readable JSON file with a `whiteList` of
`userName` entries and `userNotAllowedMessage` containing `header` and `text`.
Usernames are compared without regard to case. An absent or invalid file blocks
GitHub sign-in (503). Removing a user also revokes their session on their next
authenticated request. Health checks and GitHub sign-in endpoints stay public;
work-item, AI-model and Polarion-metadata endpoints require a session, except
for the existing public `POST /v1/work-items/ingest/import-polarion` endpoint.

Denied sign-ins redirect to `FRONTEND_URL` with `header` and `text` URL query
parameters. The frontend shows the access-denied view using these values as
untrusted text. GitHub's authorization code must be exchanged to
identify the account, but no credentials or session are stored for denied users.

## Endpoints

- `GET /health/live`
- `GET /health/ready`
- `POST /v1/work-items`
- `GET /v1/work-items/search`

See `test_main.http` for complete request examples.

## Import status

`GET /v1/polarion-metadata/import-status` requires a session and returns the
last successful full Polarion import for the active Qdrant collection, or
`null` before the first one. The response includes the UTC `completed_at`
timestamp and `processed_items` count. Imports with a `limit` and imports that
fail before index setup finishes do not change this status. It is stored in
SQLite at `SQLITE_FILE_PATH`, independently of the Qdrant collection metadata.

## Collection versioning

The Qdrant collection name is derived from:

- `QDRANT_COLLECTION_PREFIX`
- `FASTEMBED_DENSE_MODEL`
- `INDEX_SCHEMA_VERSION`

`FASTEMBED_SPARSE_MODEL`, `FASTEMBED_SPARSE_LANGUAGE` and `FASTEMBED_RERANKER_MODEL` are not part of the name but are stored as collection metadata and validated on startup, so a mismatch fails fast instead of silently corrupting the index.

This prevents vectors produced by different embedding models or schema versions from being mixed. Increment `INDEX_SCHEMA_VERSION` whenever the embedding text strategy changes incompatibly.

## Project-scoped IDs

A document's logical ID is `project_id:workitem_id`. This avoids collisions when different Polarion projects use the same work-item identifier. Search can be restricted with the `project_id` query parameter.

## Why no Celery yet?

The current synchronous Qdrant client is used from synchronous FastAPI routes, which FastAPI executes in a worker thread. A task queue should be introduced only when ingestion jobs become long-running, need retries independent of the HTTP request, or must survive API restarts.
