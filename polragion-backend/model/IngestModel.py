from typing import Any
from pydantic import BaseModel

class IngestModel(BaseModel):
    id: str
    text: str
    payload: dict[str, Any]
