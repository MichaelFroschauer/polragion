import logging
from typing import Any

from fastapi import FastAPI

from model.QdrantModel import IngestModel
from model.WorkItem import PolarionWorkItem
from vectordb.QdrantVectorDb import QdrantVectorDb

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

app = FastAPI()

db = QdrantVectorDb()
logger = logging.getLogger(__name__)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

@app.post("/v1/ingest/work_item")
async def ingest_work_item(data: PolarionWorkItem):
    try:
        db.ingest(data.to_ingest_model())
        return {"status": "ok"}
    except Exception:
        logger.exception("Qdrant ingest failed")
        raise

@app.get("/v1/search/work_item")
async def search(prompt: str) -> PolarionWorkItem:
    try:
        payloads: list[dict[str, Any]] = db.search(prompt)
        work_items = [
            PolarionWorkItem.from_dictionary(payload)
            for payload in payloads
            if payload is not None
        ]
        return work_items[0]
    except Exception:
        logger.exception("Qdrant search failed")
        raise
