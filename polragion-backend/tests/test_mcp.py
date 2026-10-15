import asyncio
import json
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from polragion.api.auth import get_current_user
from polragion.application.mcp_token_service import McpTokenService
from polragion.database.sqlite_repository import (
    SQLiteDatabase,
    SqliteMcpTokenRepository,
    SqliteUserRepository,
)
from polragion.infrastructure.mcp_auth import BackendTokenVerifier
from polragion.models.user import User
from polragion.settings import Settings


@pytest.fixture
def setup(tmp_path):
    config = tmp_path / "allowlist.json"
    config.write_text(
        json.dumps(
            {
                "whiteList": [{"userName": "Allowed"}],
                "userNotAllowedMessage": {"header": "", "text": ""},
            }
        )
    )
    settings = Settings(
        sqlite_file_path=str(tmp_path / "db.sqlite"),
        github_user_config_path=str(config),
        session_secret="test",
    )
    db = SQLiteDatabase(settings)
    users = SqliteUserRepository(db)
    user = User(github_user_id="42", username="Allowed", name="", avatar_url="")
    asyncio.run(users.create(user))
    service = McpTokenService(SqliteMcpTokenRepository(db), timedelta(days=30))
    raw, token = asyncio.run(service.create_token(user.id, "test"))
    state = SimpleNamespace(settings=settings, user_repository=users, mcp_token_service=service)
    return SimpleNamespace(
        settings=settings, config=config, db=db, user=user, state=state, raw=raw, token=token
    )


def test_allowlist_changes_and_unavailable_config(setup):
    verifier = BackendTokenVerifier(setup.state)
    assert asyncio.run(verifier.verify_token(setup.raw)).subject == str(setup.user.id)
    setup.config.write_text(
        json.dumps({"whiteList": [], "userNotAllowedMessage": {"header": "", "text": ""}})
    )
    assert asyncio.run(verifier.verify_token(setup.raw)) is None
    setup.config.write_text("invalid")
    assert asyncio.run(verifier.verify_token(setup.raw)) is None


def test_storage_expiry_and_owner_revocation(setup):
    service = setup.state.mcp_token_service
    with setup.db.transaction() as conn:
        row = conn.execute("SELECT * FROM mcp_tokens").fetchone()
        assert setup.raw not in tuple(row)
        conn.execute("UPDATE mcp_tokens SET expires_at = '2000-01-01T00:00:00+00:00'")
    assert asyncio.run(service.resolve_token(setup.raw)) is None
    assert not asyncio.run(service.revoke_token(setup.token.id, uuid4()))
    assert asyncio.run(service.revoke_token(setup.token.id, setup.user.id))
    assert asyncio.run(service.resolve_token(setup.raw)) is None


def test_parent_app_tokens_and_tool_execution(setup, monkeypatch):
    import polragion.app as backend
    from tests.fakes import FakeVectorStore

    store = FakeVectorStore()
    store.ensure_payload_indexes = Mock()
    store.search = Mock(return_value=[])
    monkeypatch.setattr(backend, "PolarionImportConfigDescriptor", lambda *args: Mock())
    monkeypatch.setattr(backend, "CopilotService", lambda *args, **kwargs: Mock())
    app = backend.create_app(
        settings=setup.settings,
        vector_store_factory=lambda settings: store,
        data_fetcher_factory=lambda settings: Mock(),
        data_worker_factory=lambda settings, service: Mock(),
    )
    headers = {
        "Accept": "application/json, text/event-stream",
        "Authorization": f"Bearer {setup.raw}",
    }
    with TestClient(app) as client:
        assert client.get("/auth/mcp-tokens").status_code == 401
        for path in ("/mcp/", "/api/mcp/"):
            listed = client.post(
                path, headers=headers, json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
            )
            assert listed.status_code == 200
            assert len(listed.json()["result"]["tools"]) == 4
        body = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "search_work_items",
                "arguments": {"params": {"search_text": "test"}},
            },
        }
        result = client.post("/mcp/", headers=headers, json=body)
        assert result.status_code == 200
        assert not result.json()["result"].get("isError")
        asyncio.run(app.state.mcp_token_service.revoke_token(setup.token.id, setup.user.id))
        assert client.post("/mcp/", headers=headers, json=body).status_code == 401
        store.search.assert_called_once()
        assert app.state.ai_tools.tools_service is app.state.work_item_tools_service
        app.dependency_overrides[get_current_user] = lambda: setup.user
        overview = client.get("/auth/mcp-tokens").json()
        assert "token_hash" not in overview["tokens"][0]
        assert "expires_at" in overview["tokens"][0]
        assert client.post("/auth/mcp-tokens", json={}).status_code == 403
        manage = {"X-MCP-Token-Management": "true"}
        assert (
            client.post(
                "/auth/mcp-tokens", headers={**manage, "Origin": "https://evil.test"}, json={}
            ).status_code
            == 403
        )
        issued = client.post("/auth/mcp-tokens", headers=manage, json={})
        assert issued.status_code == 201
        assert issued.headers["cache-control"] == "no-store"
        token_id = issued.json()["info"]["id"]
        assert client.delete(f"/auth/mcp-tokens/{token_id}", headers=manage).status_code == 204
    assert store.closed
