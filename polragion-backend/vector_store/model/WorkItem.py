from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

from vector_store.model.QdrantModel import IngestModel
from vector_store.model.VectorStoreModel import VectorStoreModel

WorkItemType = Literal[
    "requirement",
    "defect",
    "testcase",
    "task",
    "change_request",
    "risk",
]

class PolarionWorkItem(VectorStoreModel):
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

    def to_ingest_model(self) -> IngestModel:
        """Convert PolarionWorkItem to IngestModel for VectorDB."""
        embedding_text: str = f"{self.workitem_id}\n{self.title}\n\n{self.text}"
        model = IngestModel(id=self.workitem_id, text=embedding_text, payload=self.to_dictionary())
        return model


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
