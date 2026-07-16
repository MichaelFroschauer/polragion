# Architecture notes

## Dependency direction

```text
polragion.api
    -> polragion.application
        -> polragion.domain

polragion.infrastructure
    -> polragion.domain
```

The domain and application layers do not import FastAPI or Qdrant. The API layer converts HTTP requests into application-service calls. The infrastructure layer implements the `VectorStore` protocol.

## Object lifecycle

`polragion.app:create_app` creates only the FastAPI object. It does not connect to Qdrant during import.

When FastAPI enters its lifespan:

1. a `QdrantVectorStore` is created;
2. the collection is created or validated;
3. `WorkItemService` receives the vector store and mapper through constructor injection;
4. those instances are stored in `app.state`;
5. API dependency functions retrieve them for each request;
6. the vector-store client is closed during shutdown.

This is manual dependency injection. A DI container would add indirection without providing enough value at the current project size.

## Synchronous I/O

The Qdrant client is synchronous and the API route functions are ordinary `def` functions. FastAPI runs these routes in its thread pool, so blocking Qdrant calls do not run directly on the event-loop thread.

Do not change only the route to `async def` while retaining the synchronous Qdrant client. A future async conversion should switch both sides together:

```text
async route -> AsyncQdrantClient -> await
```

## Index compatibility

The collection name contains the embedding model and schema version. The adapter also verifies vector dimension and cosine distance at startup.

Increment `INDEX_SCHEMA_VERSION` whenever the text mapping changes in a way that requires re-indexing. Existing collections remain intact and a new collection is created.

## When a task queue becomes useful

Add Celery or another durable job system when ingestion:

- regularly lasts longer than an acceptable HTTP request;
- must survive an API restart;
- needs independent retries, cancellation, or progress tracking;
- should be scaled separately from HTTP traffic.

Until then, keeping ingestion synchronous avoids significant operational complexity.
