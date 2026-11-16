"""User-selected filters. None is unrestricted; an empty list matches nothing."""

from pydantic import BaseModel, ConfigDict, Field


class DocumentSelection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    project_id: str = Field(min_length=1, max_length=128)
    document_name: str = Field(min_length=1, max_length=1024)


class WorkItemFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_ids: list[str] | None = None
    project_contexts: list[str] | None = None
    document_categories: list[str] | None = None
    documents: list[DocumentSelection] | None = None
