import logging
from time import perf_counter
from typing import Any

from fastapi import FastAPI, Query
from pydantic import BaseModel
from starlette import status

from vector_store.model.WorkItem import PolarionWorkItem
from vector_store.vectordb.QdrantVectorDb import QdrantVectorDb
from vector_store.restapi.ErrorMiddleware import ErrorHandlingMiddleware

print("""
░█████████             ░██ ░█████████     ░███      ░██████  ░██                      
░██     ░██            ░██ ░██     ░██   ░██░██    ░██   ░██                          
░██     ░██  ░███████  ░██ ░██     ░██  ░██  ░██  ░██        ░██ ░███████  ░████████  
░█████████  ░██    ░██ ░██ ░█████████  ░█████████ ░██  █████ ░██░██    ░██ ░██    ░██ 
░██         ░██    ░██ ░██ ░██   ░██   ░██    ░██ ░██     ██ ░██░██    ░██ ░██    ░██ 
░██         ░██    ░██ ░██ ░██    ░██  ░██    ░██  ░██  ░███ ░██░██    ░██ ░██    ░██ 
░██          ░███████  ░██ ░██     ░██ ░██    ░██   ░█████░█ ░██ ░███████  ░██    ░██ 
© Michael Froschauer - 2026
""")

logging.basicConfig(
    level=logging.INFO,
    #level=logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(ErrorHandlingMiddleware)

db = QdrantVectorDb()

class IngestResponse(BaseModel):
    status: str
    ingested_items: int

@app.post(
    "/v1/ingest/work-item",
    response_model=IngestResponse,
    status_code=status.HTTP_200_OK,
)
def ingest_work_items(data: list[PolarionWorkItem]) -> IngestResponse:
    item_count = len(data)

    if item_count == 0:
        return IngestResponse(status="ok", ingested_items=0)

    start_time = perf_counter()

    ingest_models = [item.to_ingest_model() for item in data]
    db.ingest(ingest_models)

    duration = perf_counter() - start_time
    logger.info("Ingested %d work items in %.3f seconds", item_count, duration)

    return IngestResponse(status="ok", ingested_items=item_count)



@app.get(
    "/v1/search/work-item",
    response_model=list[PolarionWorkItem],
)
def search_work_items(prompt: str = Query(min_length=1), limit: int = Query(default=5, ge=1, le=100)) -> list[PolarionWorkItem]:
    start_time = perf_counter()

    payloads: list[dict[str, Any]] = db.search(text=prompt, limit=limit)
    work_items = [PolarionWorkItem.from_dictionary(payload) for payload in payloads]

    duration = perf_counter() - start_time
    logger.info("Work-item search returned %d results in %.3f seconds", len(work_items), duration)

    return work_items
