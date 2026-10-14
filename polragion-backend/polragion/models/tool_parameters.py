"""Shared tool schemas and descriptions for Copilot and MCP."""

from pydantic import BaseModel, Field

SEARCH_DESCRIPTION = (
    "Search indexed Polarion work items by meaning and keywords. "
    "Use get_polarion_projects to discover project IDs before filtering. "
    "For a known work item ID, use find_work_item_by_id instead."
)
LOOKUP_DESCRIPTION = "Fetch an indexed Polarion work item by its ID, optionally within a project."
PROJECTS_DESCRIPTION = "List configured Polarion projects, their descriptions and contexts."
DOCUMENTS_DESCRIPTION = "List configured Polarion documents, grouped by project and context."


class SearchWorkItemsParams(BaseModel):
    search_text: str = Field(
        min_length=1,
        max_length=10_000,
        description="Question or keywords to search for in the indexed Polarion work items.",
    )
    search_limit: int | None = Field(
        default=None,
        ge=1,
        description="Result limit; omitted uses the server default, capped at its maximum.",
    )
    search_score_threshold: float | None = Field(
        default=None,
        ge=0,
        le=1,
        description="Minimum similarity score from 0 to 1; omitted uses the server default.",
    )
    polarion_project_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=128,
        description="Project ID from get_polarion_projects; omitted searches across projects.",
    )
    reduced_work_item_size: bool = Field(
        default=False,
        description="True returns content and general information; False includes all fields.",
    )


class LookupWorkItemsParams(BaseModel):
    polarion_project_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=128,
        description="Project ID from get_polarion_projects; disambiguates work item IDs.",
    )
    polarion_work_item_id: str = Field(
        min_length=1,
        max_length=128,
        description="Exact Polarion work item ID, for example REQ-12345.",
    )
    reduced_work_item_size: bool = Field(
        default=False,
        description="True returns content and general information; False includes all fields.",
    )


class LookupDocumentsParams(BaseModel):
    polarion_project_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=128,
        description="Project ID from get_polarion_projects; omitted lists all project documents.",
    )
