import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from qdrant_client import QdrantClient, models

from polragion.api.auth import get_current_user
from polragion.api.dependencies import (
    get_ai_service,
    get_settings,
    get_user_request_manager,
    get_work_item_service,
)
from polragion.api.work_items import router
from polragion.application.search_scope import SearchScope
from polragion.application.user_request_manager import UserRequestManager
from polragion.application.work_item_mapper import WorkItemIndexMapper
from polragion.application.work_item_service import WorkItemService
from polragion.application.work_item_tools_service import WorkItemToolsService
from polragion.domain.vector_store import VectorSearchHit
from polragion.infrastructure.copilot_service import CopilotService
from polragion.infrastructure.copilot_tools import CopilotTools
from polragion.infrastructure.qdrant_hybrid_vector_store import _get_qdrant_filter
from polragion.models.ai_message import CopilotResponseMessage, CopilotSendMessage
from polragion.models.search_filters import DocumentSelection, WorkItemFilters
from polragion.models.tool_parameters import LookupWorkItemsParams, SearchWorkItemsParams
from polragion.models.user import User
from polragion.settings import Settings
from tests.factories import make_work_item


class LocalStore:
    """Use real Qdrant filtering without downloading embedding models or contacting a server."""

    def __init__(self, items):
        self.client = QdrantClient(":memory:")
        self.client.create_collection(
            "test", vectors_config=models.VectorParams(size=1, distance=models.Distance.COSINE)
        )
        self.client.upsert(
            "test",
            points=[
                models.PointStruct(
                    id=index,
                    vector=[1.0],
                    payload={
                        **item.model_dump(),
                        "_polragion_document_id": f"{item.project_id}:{item.work_item_id}",
                    },
                )
                for index, item in enumerate(items, 1)
            ],
        )
        self.calls = []

    def search(self, query, *, limit, db_filters, exact_search, **kwargs):
        self.calls.append(db_filters)
        points = self.client.query_points(
            "test", query=[1.0], limit=limit, query_filter=_get_qdrant_filter(db_filters)
        ).points
        return [
            VectorSearchHit(
                document_id=str(point.id),
                point_id=str(point.id),
                score=point.score,
                reranker_score=None,
                metadata=point.payload,
            )
            for point in points
        ]


@pytest.fixture
def services():
    items = []
    for project, name, category, contexts in [
        ("A", "Space/Shared", "system-specification", ["vehicle", "safety"]),
        ("A", "Space/Other", "software-specification", ["vehicle", "safety"]),
        ("B", "Space/Shared", "system-specification", ["safety"]),
        ("B", "Space/Other", "software-specification", ["safety"]),
        ("C", None, None, []),
    ]:
        item = make_work_item(project_id=project, workitem_id=f"REQ-{len(items)}")
        items.append(
            item.model_copy(
                update=dict(
                    document_name=name, document_category=category, project_context=contexts
                )
            )
        )
    store = LocalStore(items)
    service = WorkItemService(store, WorkItemIndexMapper())
    descriptor = Mock()
    descriptor.get_project_ids.return_value = ["A", "B", "C"]
    descriptor.get_project_context.side_effect = lambda pid: (
        ["vehicle", "safety"] if pid == "A" else ["safety"] if pid == "B" else []
    )
    descriptor.get_documents.side_effect = lambda pid: (
        ["Space/Shared", "Space/Other"] if pid != "C" else []
    )
    descriptor.get_document_category.side_effect = lambda pid, name: (
        "system-specification" if name.endswith("Shared") else "software-specification"
    )
    descriptor.get_project_description.return_value = ""
    tools = WorkItemToolsService(Settings(), service, descriptor)
    yield SimpleNamespace(items=items, store=store, service=service, tools=tools)
    store.client.close()


def ids(hits):
    return {(hit.work_item.project_id, hit.work_item.document_name) for hit in hits}


def test_default_search_includes_items_without_metadata(services):
    assert len(services.service.search("requirements", limit=20, scope=SearchScope())) == 5


@pytest.mark.parametrize(
    "field", ["project_ids", "project_contexts", "document_categories", "documents"]
)
def test_empty_group_matches_nothing_without_database_call(services, field):
    scope = SearchScope.from_filters(WorkItemFilters(**{field: []}))
    assert services.service.search("requirements", limit=10, scope=scope) == []
    assert not services.store.calls
    assert not scope.allows(services.items[0])


def test_or_within_groups_and_between_groups(services):
    scope = SearchScope.create(
        project_ids=["A", "B"],
        project_contexts=["vehicle"],
        document_categories=["system-specification"],
    )
    assert ids(services.service.search("requirements", limit=10, scope=scope)) == {
        ("A", "Space/Shared")
    }
    assert scope.allows(services.items[0])
    assert not scope.allows(services.items[2])


def test_document_pairs_are_not_cross_product_and_apply_before_limit(services):
    scope = SearchScope.create(
        documents=[
            DocumentSelection(project_id="A", document_name="Space/Other"),
            DocumentSelection(project_id="B", document_name="Space/Shared"),
        ]
    )
    assert ids(services.service.search("requirements", limit=10, scope=scope)) == {
        ("A", "Space/Other"),
        ("B", "Space/Shared"),
    }
    one = SearchScope.create(
        documents=[DocumentSelection(project_id="B", document_name="Space/Other")]
    )
    assert ids(services.service.search("requirements", limit=1, scope=one)) == {
        ("B", "Space/Other")
    }


def test_model_project_filter_only_narrows_user_scope(services):
    scope = SearchScope.create(project_ids=["A", "B"], document_categories=["system-specification"])
    assert ids(
        services.tools.search(
            SearchWorkItemsParams(search_text="req", polarion_project_id="B"), scope
        )
    ) == {("B", "Space/Shared")}
    with pytest.raises(ValueError, match="not available"):
        services.tools.search(
            SearchWorkItemsParams(search_text="req", polarion_project_id="C"), scope
        )


def test_lookup_cannot_escape_any_scope_group(services):
    params = LookupWorkItemsParams(polarion_work_item_id="REQ-0", polarion_project_id="A")
    assert services.tools.lookup(params, SearchScope.create(project_ids=["B"])) == []
    assert (
        services.tools.lookup(
            params, SearchScope.create(document_categories=["software-specification"])
        )
        == []
    )
    assert services.tools.lookup(params, SearchScope.create(project_contexts=["other"])) == []
    assert (
        services.tools.lookup(
            params,
            SearchScope.create(
                documents=[DocumentSelection(project_id="B", document_name="Space/Shared")]
            ),
        )
        == []
    )
    assert len(services.tools.lookup(params)) == 1


def test_discovery_tools_obey_scope(services):
    scope = SearchScope.create(
        documents=[DocumentSelection(project_id="B", document_name="Space/Shared")]
    )
    assert [project["project_id"] for project in json.loads(services.tools.projects(scope))] == [
        "B"
    ]
    assert json.loads(services.tools.documents(None, scope))[0]["documents"] == ["Space/Shared"]
    assert json.loads(services.tools.documents("A", scope)) == []
    assert json.loads(services.tools.projects(SearchScope(match_none=True))) == []


def make_api(services, ai):
    app = FastAPI()
    app.include_router(router)
    user = User(github_user_id="1", username="test", name="", avatar_url="")
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_settings] = lambda: Settings()
    app.dependency_overrides[get_work_item_service] = lambda: services.service
    app.dependency_overrides[get_ai_service] = lambda: ai
    manager = UserRequestManager(Settings())
    app.dependency_overrides[get_user_request_manager] = lambda: manager
    return app


def test_search_api_default_partial_and_empty_filters(services):
    with TestClient(make_api(services, Mock())) as client:
        assert (
            len(client.post("/v1/work-items/search", json={"prompt": "req"}).json()["work_items"])
            == 5
        )
        response = client.post(
            "/v1/work-items/search", json={"prompt": "req", "filters": {"project_ids": ["B"]}}
        )
        assert response.status_code == 200
        assert {hit["work_item"]["project_id"] for hit in response.json()["work_items"]} == {"B"}
        assert (
            client.post(
                "/v1/work-items/search", json={"prompt": "req", "filters": {"project_ids": []}}
            ).json()["work_items"]
            == []
        )
        assert (
            client.post(
                "/v1/work-items/search",
                json={
                    "prompt": "req",
                    "filters": {
                        "documents": [{"project_id": "B", "document_name": "Space/Shared"}]
                    },
                },
            ).status_code
            == 200
        )
        assert client.get("/v1/work-items/search", params={"prompt": "req"}).status_code == 405


def test_ask_passes_a_new_scope_each_time(services):
    ai = SimpleNamespace(send_message=AsyncMock(return_value=CopilotResponseMessage(text="ok")))
    app = make_api(services, ai)
    contexts = []
    with TestClient(app) as client:
        for filters in ({"project_ids": ["A"]}, {"project_ids": []}, {}):
            response = client.post("/v1/work-items/ask", json={"prompt": "req", "filters": filters})
            assert response.status_code == 200
            context = ai.send_message.call_args.args[0].request_context
            contexts.append(context)
            assert context.search_scope == SearchScope.from_filters(WorkItemFilters(**filters))
            manager = app.dependency_overrides[get_user_request_manager]()
            assert manager.get_active(context.user_id) is None
    assert len({context.request_id for context in contexts}) == len(contexts)


def test_api_exposes_only_the_current_search_and_ask_contract(services):
    app = make_api(services, Mock())
    paths = app.openapi()["paths"]
    assert set(paths["/v1/work-items/search"]) == {"post"}
    assert "/v1/work-items/ask-with-search" not in paths
    parameters = paths["/v1/work-items/ask"]["post"].get("parameters", [])
    assert {parameter["name"] for parameter in parameters} == {"answer_detail"}
    with TestClient(app) as client:
        assert (
            client.post("/v1/work-items/ask-with-search", json={"prompt": "req"}).status_code == 404
        )


def test_copilot_tools_use_current_scope_even_when_session_tools_are_reused(services):
    async def run():
        manager = UserRequestManager(Settings())
        user = uuid4()
        tools = {
            tool.name: tool
            for tool in CopilotTools(
                tools_service=services.tools, user_request_manager=manager
            ).create_tools(user)
        }
        manager.start_request(manager.create_request(user, SearchScope.create(project_ids=["B"])))
        lookup = await tools["find_work_item_by_id"].handler(
            SimpleNamespace(
                arguments={"polarion_project_id": "A", "polarion_work_item_id": "REQ-0"}
            )
        )
        assert "not found" in lookup.text_result_for_llm
        results = await tools["vector_db_work_items_search"].handler(
            SimpleNamespace(arguments={"search_text": "req"})
        )
        assert {
            row["work_item"]["project_id"] for row in json.loads(results.text_result_for_llm)
        } == {"B"}
        projects = await tools["get_polarion_projects"].handler(SimpleNamespace(arguments={}))
        assert [row["project_id"] for row in json.loads(projects.text_result_for_llm)] == ["B"]
        documents = await tools["get_polarion_documents"].handler(SimpleNamespace(arguments={}))
        assert [row["project_id"] for row in json.loads(documents.text_result_for_llm)] == ["B"]
        assert len(manager.get_active(user).collected_work_items()) == 2
        manager.finish_request(user)
        manager.start_request(manager.create_request(user))
        results = await tools["vector_db_work_items_search"].handler(
            SimpleNamespace(arguments={"search_text": "req"})
        )
        assert len(json.loads(results.text_result_for_llm)) == 5
        manager.finish_request(user)
        assert manager.active_search_scope(user).is_empty()

    asyncio.run(run())


def test_parallel_requests_keep_their_scope_until_completion(services):
    from polragion.infrastructure.copilot_service import AssistantMessageData

    async def run():
        manager = UserRequestManager(Settings())
        service = object.__new__(CopilotService)
        service._user_locks = {}
        service._user_request_manager = manager
        service.initialize = AsyncMock()
        service._disconnect_user_session = AsyncMock()
        user = uuid4()
        entered = asyncio.Event()
        release = asyncio.Event()
        seen = []

        async def send(**kwargs):
            context = manager.get_active(user)
            seen.append(context.search_scope)
            assert "current_request_filters" in kwargs["prompt"]
            assert "These filters apply only to this request" in kwargs["prompt"]
            if len(seen) == 1:
                entered.set()
                await release.wait()
                assert manager.get_active(user) is context
            return SimpleNamespace(data=AssistantMessageData(content="ok", message_id="reply"))

        session = SimpleNamespace(
            rpc=SimpleNamespace(
                usage=SimpleNamespace(
                    get_metrics=AsyncMock(return_value=SimpleNamespace(total_nano_aiu=0))
                )
            ),
            send_and_wait=send,
        )
        service._get_user_session = AsyncMock(return_value=session)
        first_scope = SearchScope.create(project_ids=["A"])
        first_context = manager.create_request(user, first_scope)
        first_context.tool_call_budget.used = 1
        initial_hits = services.service.search("req", limit=1, scope=first_scope)
        await first_context.add_work_items(initial_hits)
        assert manager.get_active(user) is None
        first = asyncio.create_task(
            service.send_message(
                CopilotSendMessage(user_id=user, text="first", request_context=first_context)
            )
        )
        await entered.wait()
        second_context = manager.create_request(user)
        assert manager.get_active(user) is first_context
        second = asyncio.create_task(
            service.send_message(
                CopilotSendMessage(user_id=user, text="second", request_context=second_context)
            )
        )
        await asyncio.sleep(0)
        assert manager.active_search_scope(user) == first_scope
        release.set()
        responses = await asyncio.gather(first, second)
        assert seen == [first_scope, SearchScope()]
        assert responses[0].request_context is first_context
        assert responses[1].request_context is second_context
        assert first_context.tool_call_budget.used == 1
        assert first_context.collected_work_items() == initial_hits
        assert first_context.request_id != second_context.request_id
        assert manager.get_active(user) is None

        fallback = await service.send_message(CopilotSendMessage(user_id=user, text="no context"))
        assert fallback.request_context.search_scope.is_empty()
        assert fallback.request_context.request_id not in {
            first_context.request_id,
            second_context.request_id,
        }
        assert manager.get_active(user) is None

        session.send_and_wait = AsyncMock(side_effect=RuntimeError("test failure"))
        with pytest.raises(Exception, match="Copilot request failed"):
            await service.send_message(
                CopilotSendMessage(
                    user_id=user,
                    text="fail",
                    request_context=manager.create_request(user, first_scope),
                )
            )
        assert manager.get_active(user) is None
        with pytest.raises(ValueError, match="user_id must match"):
            await service.send_message(
                CopilotSendMessage(
                    user_id=user,
                    text="wrong owner",
                    request_context=manager.create_request(uuid4()),
                )
            )
        assert manager.get_active(user) is None

    asyncio.run(run())


def test_hybrid_search_filters_each_prefetch_before_candidate_limit():
    from polragion.infrastructure.db_filter import DbFilter
    from polragion.infrastructure.qdrant_hybrid_vector_store import QdrantHybridVectorStore

    store = object.__new__(QdrantHybridVectorStore)
    store._ensure_initialized = Mock()
    store._candidate_limit = 50
    store._collection_name = "test"
    store._make_dense_query_embedding = Mock(return_value=[1.0])
    store._make_sparse_query_embedding = Mock(
        return_value=models.SparseVector(indices=[1], values=[1.0])
    )
    store._client = Mock()
    store._client.query_points.return_value = SimpleNamespace(points=[])
    store.search("req", limit=1, db_filters=[DbFilter(key="project_id", value="B")])
    kwargs = store._client.query_points.call_args.kwargs
    assert all(prefetch.filter == kwargs["query_filter"] for prefetch in kwargs["prefetch"])
