from pydantic import BaseModel, ConfigDict, Field

from polragion.models.work_item import PolarionWorkItem


class IngestResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    ingested_items: int = Field(ge=0)


class WorkItemSearchHit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    work_item: PolarionWorkItem
    score: float
    point_id: str


class WorkItemSearchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    work_items: list[WorkItemSearchHit]


class WorkItemAskResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str
    tokens_spent: int
    work_items: list[WorkItemSearchHit]


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
