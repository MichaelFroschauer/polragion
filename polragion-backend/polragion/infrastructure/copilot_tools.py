import asyncio
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from uuid import UUID

from copilot import PreToolUseHookInput, PreToolUseHookOutput, Tool, define_tool
from starlette.concurrency import run_in_threadpool

from polragion.application.work_item_tools_service import WorkItemToolsService
from polragion.models.tool_parameters import (
    DOCUMENTS_DESCRIPTION,
    LOOKUP_DESCRIPTION,
    PROJECTS_DESCRIPTION,
    SEARCH_DESCRIPTION,
    LookupDocumentsParams,
    LookupWorkItemsParams,
    SearchWorkItemsParams,
)

if TYPE_CHECKING:
    from polragion.application.user_request_manager import UserRequestManager

logger = logging.getLogger(__name__)


class CopilotTools:
    def __init__(
        self, *, tools_service: WorkItemToolsService, user_request_manager: "UserRequestManager"
    ) -> None:
        self.tools_service = tools_service
        self.user_request_manager = user_request_manager

    def create_tools(self, user_id: UUID) -> list[Tool]:
        return [
            self._create_work_item_vector_search_tool(user_id),
            self._create_work_item_id_search_tool(user_id),
            self._create_project_fetcher_tool(),
            self._create_document_fetcher_tool(),
        ]

    def _create_work_item_vector_search_tool(self, user_id: UUID) -> Tool:
        @define_tool(description=SEARCH_DESCRIPTION)
        async def vector_db_work_items_search(params: SearchWorkItemsParams) -> str:
            scope = self.user_request_manager.active_search_scope(user_id)
            try:
                results = await run_in_threadpool(self.tools_service.search, params, scope)
            except ValueError as exc:
                return str(exc)
            await self.user_request_manager.add_searched_work_items(user_id, results)
            return self.tools_service.format_results(results, params.reduced_work_item_size)

        return vector_db_work_items_search

    def _create_work_item_id_search_tool(self, user_id: UUID) -> Tool:
        @define_tool(description=LOOKUP_DESCRIPTION)
        async def find_work_item_by_id(params: LookupWorkItemsParams) -> str:
            try:
                results = await run_in_threadpool(self.tools_service.lookup, params)
            except ValueError as exc:
                return str(exc)
            if not results:
                return (
                    f"Work item for project ID: {params.polarion_project_id} "
                    f"work item ID: {params.polarion_work_item_id} not found."
                )
            await self.user_request_manager.add_searched_work_items(user_id, results)
            return self.tools_service.format_results(results, params.reduced_work_item_size)

        return find_work_item_by_id

    def _create_project_fetcher_tool(self) -> Tool:
        @define_tool(description=PROJECTS_DESCRIPTION)
        async def get_polarion_projects() -> str:
            return await run_in_threadpool(self.tools_service.projects)

        return get_polarion_projects

    def _create_document_fetcher_tool(self) -> Tool:
        @define_tool(description=DOCUMENTS_DESCRIPTION)
        async def get_polarion_documents(params: LookupDocumentsParams) -> str:
            return await run_in_threadpool(self.tools_service.documents, params.polarion_project_id)

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


async def check_tool_budget(
    input_data: PreToolUseHookInput, user_request_manager: "UserRequestManager", user_id: UUID
) -> PreToolUseHookOutput:
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
        logger.warning(
            "Copilot tool limit reached: user=%s tool=%s used=%d max=%d",
            user_id,
            tool_name,
            used,
            budget.max_calls,
        )

        return PreToolUseHookOutput(
            permissionDecision="deny",
            permissionDecisionReason=(
                f"The maximum of {budget.max_calls} tool calls for this "
                "user request has been reached. Do not call any more tools. "
                "Answer the user using the information already collected."
            ),
        )

    logger.info(
        "Copilot tool call %d/%d: user=%s tool=%s arguments=%s",
        used,
        budget.max_calls,
        user_id,
        tool_name,
        tool_args,
    )

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
