from pydantic import BaseModel, ConfigDict, Field

from polragion.models.work_item import WorkItemSearchHit


class IngestResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    ingested_items: int = Field(ge=0)


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
