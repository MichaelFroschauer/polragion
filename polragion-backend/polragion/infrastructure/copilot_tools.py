import asyncio
import logging
from dataclasses import dataclass, field
from uuid import UUID

from copilot import define_tool, Tool, PreToolUseHookOutput, PreToolUseHookInput
from pydantic import BaseModel, Field

from polragion.application.work_item_mapper import work_item_search_hit_to_json_str
from polragion.application.work_item_service import WorkItemService
from polragion.domain.vector_store import VectorStore
from polragion.models.work_item import WorkItemSearchHit, ReducedWorkItem, PolarionWorkItem
from polragion.settings import Settings

logger = logging.getLogger(__name__)

class CopilotTools:

    def __init__(
            self,
            settings: Settings,
            work_item_service: WorkItemService,
            vector_store: VectorStore,
    ) -> None:
        self.settings = settings
        self.work_item_service = work_item_service
        self._vector_store = vector_store

    def create_tools(self) -> list:
        return [
            self._create_work_item_vector_search_tool(),
            self._create_work_item_id_search_tool(),
            self._create_distinct_project_id_fetcher_tool(),
        ]

    def _create_work_item_vector_search_tool(self) -> Tool:

        service = self.work_item_service

        class SearchWorkItemsParams(BaseModel):
            search_text: str = Field(description="Text prompt with questions and keywords that should be searched in the Polragion vector database (Must be english!).")
            search_limit: int | None = Field(default=None, description="Optional limit for the number of results to return.")
            search_score_threshold: float | None = Field(default=None, gt=0, le=1, description="Optional score threshold for the search results (Must be between 0 and 1).")
            polarion_project_id: str | None = Field(default=None, description="Optional Polarion project ID.")

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

            json_str = work_item_search_hit_to_json_str(results)
            return json_str

        return vector_db_work_items_search


    def _create_work_item_id_search_tool(self) -> Tool:

        service = self.work_item_service

        class LookupWorkItemsParams(BaseModel):
            polarion_project_id: str | None = Field(default=None, description="Polarion project ID.")
            polarion_work_item_id: str | None = Field(default=None, description="Polarion work item ID (Like: PREFIX-12345).")

        @define_tool(description="Fetch a specific polarion work items via its ID.")
        async def find_work_item_by_id(params: LookupWorkItemsParams) -> str:

            if params.polarion_project_id is None:
                return "Polarion project ID not provided"

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

            found_work_item: PolarionWorkItem = results[0].work_item
            work_item = ReducedWorkItem.from_work_item(found_work_item).model_dump(mode="json", by_alias=True)

            return work_item

        return find_work_item_by_id


    def _create_distinct_project_id_fetcher_tool(self) -> Tool:

        service = self.work_item_service

        @define_tool(description="Get a list of distinct available Polarion project IDs in the vector database.")
        async def get_distinct_polarion_projects() -> str:

            project_ids = self._vector_store.get_facet("project_id")
            project_ids_str = ' '.join([str(project_id) for project_id in project_ids])

            return project_ids_str

        return get_distinct_polarion_projects


@dataclass
class ToolCallBudget:
    max_calls: int
    used: int = 0
    active: bool = False
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def start_request(self) -> None:
        async with self.lock:
            self.used = 0
            self.active = True

    async def finish_request(self) -> int:
        async with self.lock:
            self.active = False
            return self.used

    async def try_consume(self) -> tuple[bool, int]:
        async with self.lock:
            if not self.active:
                return False, self.used

            if self.used >= self.max_calls:
                return False, self.used

            self.used += 1
            return True, self.used



async def check_tool_budget(input_data: PreToolUseHookInput, budget: ToolCallBudget, user_id: UUID) -> PreToolUseHookOutput:
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
