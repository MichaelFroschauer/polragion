from pydantic import BaseModel, ConfigDict, Field

from polragion.domain.work_item import PolarionWorkItem


class IngestResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    ingested_items: int = Field(ge=0)


class WorkItemSearchHitResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    work_item: PolarionWorkItem
    score: float
    point_id: str


class HealthResponse(BaseModel):
    status: str
