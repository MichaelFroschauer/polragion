import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from uuid import UUID

from copilot import define_tool, Tool, PreToolUseHookOutput, PreToolUseHookInput
from pydantic import BaseModel, Field

from polragion.application.work_item_mapper import work_item_search_hit_to_json_str
from polragion.application.work_item_service import WorkItemService
from polragion.domain.polarion_descriptor import PolarionDescriptor
from polragion.domain.vector_store import VectorStore
from polragion.models.work_item import WorkItemSearchHit
from polragion.settings import Settings

# Imported only for type hints; a runtime import would create a circular
if TYPE_CHECKING:
    from polragion.application.user_request_manager import UserRequestManager

logger = logging.getLogger(__name__)

class CopilotTools:

    def __init__(
            self, *,
            settings: Settings,
            work_item_service: WorkItemService,
            user_request_manager: "UserRequestManager",
            vector_store: VectorStore,
            polarion_descriptor: PolarionDescriptor,
    ) -> None:
        self.settings = settings
        self.work_item_service = work_item_service
        self.user_request_manager = user_request_manager
        self._vector_store = vector_store
        self._polarion_descriptor: PolarionDescriptor = polarion_descriptor

    def create_tools(self, user_id: UUID) -> list:
        return [
            self._create_work_item_vector_search_tool(user_id),
            self._create_work_item_id_search_tool(user_id),
            self._create_project_fetcher_tool(),
            self._create_document_fetcher_tool(),
        ]

    def _create_work_item_vector_search_tool(self, user_id: UUID) -> Tool:

        service = self.work_item_service

        # TODO: Only captured once at tool-creation time as closure vars (not model fields).
        project_ids = self._vector_store.get_facet("project_id")
        project_ids_str = ", ".join(str(project_id) for project_id in project_ids)

        class SearchWorkItemsParams(BaseModel):
            search_text: str = Field(description="Text prompt with questions and keywords that should be searched in the Polragion vector database (Must be english!).")
            search_limit: int | None = Field(default=None, description="Optional limit for the number of results to return.")
            search_score_threshold: float | None = Field(default=None, gt=0, le=1, description="Optional score threshold for the search results (Must be between 0 and 1).")
            polarion_project_id: str | None = Field(default=None, description=f"Optional Polarion project ID. Available project IDs: {project_ids_str}")
            reduced_work_item_size: bool = Field(default=False, description=f"Optional: If False every available information and field is shown for the work item. This is not needed if only the content and general information is required.")

        @define_tool(description="Fetch information details from the vector database that contains all polarion work items.")
        async def vector_db_work_items_search(params: SearchWorkItemsParams) -> str:
            limit = params.search_limit if params.search_limit is not None else self.settings.search_default_limit
            limit = min(limit, self.settings.search_max_limit)

            threshold = params.search_score_threshold
            if threshold is None:
                threshold = self.settings.search_score_threshold
            if threshold is None:
                threshold = 0.0
            threshold = min(max(threshold, 0.0), 1.0)

            results: list[WorkItemSearchHit] = service.search(
                params.search_text,
                limit=limit,
                score_threshold=threshold,
                project_id=params.polarion_project_id,
                do_reranking=False,
            )

            await self.user_request_manager.add_searched_work_items(user_id, results)

            json_str = work_item_search_hit_to_json_str(results, reduced_information=params.reduced_work_item_size)

            return json_str

        return vector_db_work_items_search


    def _create_work_item_id_search_tool(self, user_id: UUID) -> Tool:

        service = self.work_item_service

        # TODO: Only captured once at tool-creation time as closure vars (not model fields).
        project_ids = self._vector_store.get_facet("project_id")
        project_ids_str = ", ".join(str(project_id) for project_id in project_ids)

        class LookupWorkItemsParams(BaseModel):
            polarion_project_id: str | None = Field(default=None, description=f"Optional Polarion project ID. Available project IDs: {project_ids_str}")
            polarion_work_item_id: str | None = Field(default=None, description="Polarion work item ID (Like: PREFIX-12345).")
            reduced_work_item_size: bool = Field(default=False, description=f"Optional: If False every available information and field is shown for the work item. This is not needed if only the content and general information is required.")

        @define_tool(description="Fetch a specific polarion work items via its ID.")
        async def find_work_item_by_id(params: LookupWorkItemsParams) -> str:

            if params.polarion_work_item_id is None:
                return "Polarion work item ID not provided"

            results: list[WorkItemSearchHit] = service.search(
                "",
                limit=1,
                score_threshold=0.0,
                project_id=params.polarion_project_id,
                work_item_id=params.polarion_work_item_id,
            )

            if len(results) == 0:
                return (f"Work item for project ID: {params.polarion_project_id} "
                        f"work item ID: {params.polarion_work_item_id} not found.")

            await self.user_request_manager.add_searched_work_items(user_id, results)

            json_str = work_item_search_hit_to_json_str(results, reduced_information=params.reduced_work_item_size)

            return json_str

        return find_work_item_by_id


    def _create_project_fetcher_tool(self) -> Tool:

        @define_tool(description="Get a list of available Polarion projects and their responding information (mostly for further tool calls).")
        async def get_polarion_projects() -> str:

            project_desc: list[dict] = []
            for project_id in self._polarion_descriptor.get_project_ids():
                p_description: str = self._polarion_descriptor.get_project_description(project_id) or ""
                p_context: list[str] = self._polarion_descriptor.get_project_context(project_id)

                project_desc.append({
                    "project_id": project_id,
                    "project_description": p_description,
                    "project_context": p_context,
                })

            return json.dumps(project_desc)

            # TODO: Old code, remove after new code is tested
            # project_ids = self._vector_store.get_facet("project_id")
            # project_ids_str = ' '.join([str(project_id) for project_id in project_ids])
            #
            # return project_ids_str

        return get_polarion_projects


    def _create_document_fetcher_tool(self) -> Tool:

        service = self.work_item_service

        # TODO: Only captured once at tool-creation time as closure vars (not model fields).
        project_ids = self._vector_store.get_facet("project_id")
        project_ids_str = ", ".join(str(project_id) for project_id in project_ids)

        class LookupDocumentsParams(BaseModel):
            polarion_project_id: str | None = Field(default=None, description=f"Optional Polarion project ID. Available project IDs: {project_ids_str}")

        @define_tool(description="Get a list of available Polarion documents and their responding information (mostly for further tool calls).")
        async def get_polarion_documents(params: LookupDocumentsParams) -> str:

            project_ids: list[str] = []
            if params.polarion_project_id:
                project_ids.append(params.polarion_project_id)
            else:
                project_ids = self._polarion_descriptor.get_project_ids()

            project_docs: list[dict] = []
            for project_id in project_ids:
                project_context = self._polarion_descriptor.get_project_context(project_id)
                document_names = self._polarion_descriptor.get_documents(project_id)
                project_docs.append({
                    "project_id": project_id,
                    "project_context": project_context,
                    "documents": document_names,
                })

            return json.dumps(project_docs)

        return get_polarion_documents


@dataclass
class ToolCallBudget:
    max_calls: int
    used: int = 0
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def try_consume(self) -> tuple[bool, int]:
        async with self.lock:
            if self.used >= self.max_calls:
                return False, self.used

            self.used += 1
            return True, self.used



async def check_tool_budget(input_data: PreToolUseHookInput, user_request_manager: "UserRequestManager", user_id: UUID) -> PreToolUseHookOutput:
    context = user_request_manager.get_active(user_id)
    if context is None:
        return PreToolUseHookOutput(
            permissionDecision="deny",
            permissionDecisionReason="No active request context; tool calls are not allowed.",
        )

    budget = context.tool_call_budget
    allowed, used = await budget.try_consume()

    tool_name = input_data.get("toolName", "UNDEFINED")
    tool_args = input_data.get("toolArgs", "")

    if not allowed:
        logger.warning("Copilot tool limit reached: user=%s tool=%s used=%d max=%d", user_id, tool_name, used, budget.max_calls)

        return PreToolUseHookOutput(
            permissionDecision="deny",
            permissionDecisionReason= (
                f"The maximum of {budget.max_calls} tool calls for this "
                "user request has been reached. Do not call any more tools. "
                "Answer the user using the information already collected."
            )
        )

    logger.info("Copilot tool call %d/%d: user=%s tool=%s arguments=%s", used, budget.max_calls, user_id, tool_name, tool_args)

    if used == budget.max_calls:
        return PreToolUseHookOutput(
            permissionDecision="allow",
            additionalContext=(
                "This is the final tool call available for this user request. "
                "After receiving its result, answer the user without using "
                "any additional tools."
            ),
        )

    return PreToolUseHookOutput(permissionDecision="allow")
