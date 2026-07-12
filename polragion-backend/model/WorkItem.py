from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

from model.IngestModel import IngestModel

WorkItemType = Literal[
    "requirement",
    "defect",
    "testcase",
    "task",
    "change_request",
    "risk",
]


class LinkedWorkItem(BaseModel):
    id: str
    role: str


class CustomFields(BaseModel):
    model_config = ConfigDict(extra="ignore")

    workitem_type: WorkItemType

    priority: str | None = None
    severity: str | None = None

    author: str | None = None
    assignee: str | None = None

    created: datetime | None = None
    updated: datetime | None = None
    due_date: date | None = None

    safety_class: str | None = None
    requirement_category: str | None = None

    tags: list[str] = Field(default_factory=list)


class PolarionWorkItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    text: str

    revision: int = Field(ge=1)
    status: str
    workitem_id: str

    linked_workitems: list[LinkedWorkItem] = Field(
        default_factory=list
    )

    custom_fields: CustomFields

    @property
    def embedding_text(self) -> str:
        """Text that is sent to the embedding service."""
        return f"{self.workitem_id}\n{self.title}\n\n{self.text}"

    def to_dictionary(self) -> dict:
        """JSON-Compatible Qdrant-Payload."""
        return self.model_dump(mode="json")

    def to_ingest_model(self) -> IngestModel:
        model = IngestModel(id=self.workitem_id, text=self.embedding_text, payload=self.to_dictionary())
        return model
