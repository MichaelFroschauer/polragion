import asyncio
from dataclasses import dataclass, field
from uuid import UUID, uuid4

from polragion.application.search_scope import SearchScope
from polragion.infrastructure.copilot_tools import ToolCallBudget
from polragion.models.work_item import WorkItemSearchHit
from polragion.settings import Settings


@dataclass
class RequestContext:
    """Per-request state shared across a single AI request.

    A new context is created for each ``send_message`` call and identified by
    its own ``request_id``. It stays alive across the request's tool calls, so
    e.g. work items fetched from the vector DB can be collected and returned.
    """

    request_id: UUID
    user_id: UUID
    tool_call_budget: ToolCallBudget
    search_scope: SearchScope = field(default_factory=SearchScope)
    _work_items: list[WorkItemSearchHit] = field(default_factory=list)
    _seen_point_ids: set[str] = field(default_factory=set)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def add_work_items(self, hits: list[WorkItemSearchHit]) -> None:
        async with self._lock:
            for hit in hits:
                if hit.point_id in self._seen_point_ids:
                    continue
                self._seen_point_ids.add(hit.point_id)
                self._work_items.append(hit)

    def collected_work_items(self) -> list[WorkItemSearchHit]:
        return list(self._work_items)


class UserRequestManager:
    """Tracks the active :class:`RequestContext` per user.

    Requests are serialized per user by ``CopilotService``, so at most one
    request context is active per user at any time.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._active: dict[UUID, RequestContext] = {}

    def start_request(self, user_id: UUID, search_scope: SearchScope | None = None) -> RequestContext:
        context = RequestContext(
            request_id=uuid4(),
            user_id=user_id,
            tool_call_budget=ToolCallBudget(max_calls=self._settings.max_allowed_tool_calls),
            search_scope=search_scope or SearchScope(),
        )
        self._active[user_id] = context
        return context

    def get_active(self, user_id: UUID) -> RequestContext | None:
        return self._active.get(user_id)

    def active_search_scope(self, user_id: UUID) -> SearchScope:
        context = self._active.get(user_id)
        return context.search_scope if context else SearchScope()

    def finish_request(self, user_id: UUID) -> RequestContext | None:
        return self._active.pop(user_id, None)

    async def add_searched_work_items(self, user_id: UUID, hits: list[WorkItemSearchHit]) -> None:
        context = self._active.get(user_id)
        if context is None:
            return
        await context.add_work_items(hits)

    def shutdown(self) -> None:
        self._active.clear()
