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


class PolarionDocumentMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    category: str


class PolarionProjectMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    contexts: list[str]
    documents: list[PolarionDocumentMetadata]


class PolarionMetadataResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_ids: list[str]
    project_contexts: list[str]
    project_categories: list[str]
    projects: list[PolarionProjectMetadata]
