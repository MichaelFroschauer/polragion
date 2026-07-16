# Migration from version 0.1

## Start command

Preferred:

```bash
uv run uvicorn polragion.app:app --reload
```

The old `vector_store.main:app` and `ai_connector.main:app` paths remain as compatibility shims and expose the same application.

## Endpoint changes

| Old | New |
|---|---|
| `POST /v1/ingest/work-item` | `POST /v1/work-items` |
| `GET /v1/search/work-item` | `GET /v1/work-items/search` |

The new search response wraps each work item with its similarity `score` and Qdrant `point_id`.

## Data model change

`project_id` is now required. Stable vector IDs are generated from:

```text
project_id:workitem_id
```

This prevents identically named work items from different Polarion projects overwriting each other.

## Environment variables

Copy `.env.example` to `.env`. The previous variables have been renamed for consistency:

| Previous | Current |
|---|---|
| `QDRANT_COLLECTION_NAME` | `QDRANT_COLLECTION_PREFIX` |
| `FASTEMBED_BATCH_SIZE` | `QDRANT_BATCH_SIZE` |
| `FASTEMBED_PARALLEL` | `QDRANT_PARALLEL` |

`FASTEMBED_MODEL` and `QDRANT_URL` remain unchanged.

## Existing vectors

The refactored application intentionally uses a new, model-versioned collection name. Existing points are not migrated automatically because their payload lacks `project_id`, and their embedding text was generated using the old mapping. Re-ingest the Polarion work items after starting the new version.
