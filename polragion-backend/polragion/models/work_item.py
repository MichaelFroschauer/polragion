from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class LinkedWorkItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=128)
    role: str = Field(min_length=1, max_length=128)
    direction: Literal["outgoing", "incoming"]


class CustomFields(BaseModel):
    # Polarion installations often have additional custom fields. Unknown fields
    # are intentionally ignored here so the API remains forwards-compatible.
    model_config = ConfigDict(extra="ignore")

    safety_requirement: str | None = Field(default=None, max_length=128)


class PolarionWorkItem(BaseModel):
    """Validated domain representation of a Polarion work item."""

    model_config = ConfigDict(extra="ignore")

    project_id: str = Field(min_length=1, max_length=128)
    project_name: str | None = Field(default=None, max_length=128)

    work_item_id: str = Field(min_length=1, max_length=128)
    work_item_type:  str = Field(min_length=1, max_length=128)

    document_name: str | None = Field(default=None, max_length=1024)
    document_category: str | None = Field(default=None, max_length=128)

    title: str = Field(default="", max_length=5_000)
    description: str | None = Field(default=None, max_length=500_000)

    revision: int = Field(ge=1)
    status: str | None = Field(default=None, max_length=128)
    location: str | None = Field(default=None, max_length=1024)

    linked_work_items: list[LinkedWorkItem] = Field(
        default_factory=list,
        max_length=1_000,
    )

    custom_fields: CustomFields = Field(
        default_factory=CustomFields
    )


class ReducedWorkItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: str = Field(min_length=1, max_length=128)
    work_item_id: str = Field(min_length=1, max_length=128)
    work_item_type: str = Field(min_length=1, max_length=128)

    title: str = Field(default="", max_length=5_000)
    description: str | None = Field(default=None, max_length=500_000)

    @classmethod
    def from_work_item(cls, work_item: PolarionWorkItem) -> ReducedWorkItem:
        reduced = cls.model_validate(
            work_item.model_dump(
                include=set(cls.model_fields)
            )
        )
        return reduced
