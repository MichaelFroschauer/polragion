import logging
from typing import Any

from fastapi import FastAPI
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

@app.post("/v1/ingest/work_item")
async def ingest_work_item(data: list[PolarionWorkItem]):
    try:
        #db.ingest(data.to_ingest_model())
        for work_item in data:
            db.ingest(work_item.to_ingest_model())
        return {"status": "ok"}
    except Exception:
        logger.exception("Vector database ingest failed")
        raise

@app.get("/v1/search/work_item")
async def search(prompt: str) -> list[PolarionWorkItem]:
    try:
        payloads: list[dict[str, Any]] = db.search(prompt)
        work_items = [
            PolarionWorkItem.from_dictionary(payload)
            for payload in payloads
            if payload is not None
        ]
        return work_items
    except Exception:
        logger.exception("Vector database search failed")
        raise
