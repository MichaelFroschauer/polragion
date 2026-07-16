from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

WorkItemType = Literal[
    "requirement",
    "defect",
    "testcase",
    "task",
    "change_request",
    "risk",
]


class LinkedWorkItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=128)
    role: str = Field(min_length=1, max_length=128)


class CustomFields(BaseModel):
    # Polarion installations often have additional custom fields. Unknown fields
    # are intentionally ignored here so the API remains forwards-compatible.
    model_config = ConfigDict(extra="ignore")

    workitem_type: WorkItemType

    priority: str | None = Field(default=None, max_length=128)
    severity: str | None = Field(default=None, max_length=128)

    author: str | None = Field(default=None, max_length=256)
    assignee: str | None = Field(default=None, max_length=256)

    created: datetime | None = None
    updated: datetime | None = None
    due_date: date | None = None

    safety_class: str | None = Field(default=None, max_length=128)
    requirement_category: str | None = Field(default=None, max_length=256)

    tags: list[str] = Field(default_factory=list, max_length=100)


class PolarionWorkItem(BaseModel):
    """Validated domain representation of a Polarion work item."""

    model_config = ConfigDict(extra="forbid")

    project_id: str = Field(min_length=1, max_length=128)
    workitem_id: str = Field(min_length=1, max_length=128)

    title: str = Field(min_length=1, max_length=5_000)
    text: str = Field(min_length=1, max_length=500_000)

    revision: int = Field(ge=1)
    status: str = Field(min_length=1, max_length=128)

    linked_workitems: list[LinkedWorkItem] = Field(
        default_factory=list,
        max_length=1_000,
    )
    custom_fields: CustomFields
