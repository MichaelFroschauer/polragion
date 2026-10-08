import json
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from urllib.parse import parse_qs, urlsplit

import pytest
from cryptography.fernet import Fernet
from fastapi import FastAPI
from fastapi.testclient import TestClient
from polragion.api import auth
from polragion.api.dependencies import (
    get_data_fetcher,
    get_data_worker,
    get_github_credentials_repository,
    get_import_status_repository,
    get_session_service,
    get_settings,
    get_user_repository,
    get_work_item_service,
)
from polragion.api.polarion_metadata import router as metadata_router
from polragion.api.work_items import router as work_items_router, public_router as public_work_items_router
from polragion.database.sqlite_repository import SQLiteDatabase, SqliteImportStatusRepository
from polragion.models.user import OAuthToken, User, UserSession
from polragion.settings import Settings
from polragion.utils.general import utc_now
from starlette.middleware.sessions import SessionMiddleware


@pytest.fixture
def auth_setup(tmp_path, monkeypatch):
    config_path = tmp_path / "github-user-config.json"
    config_path.write_text(json.dumps({
        "whiteList": [{"userName": "AllowedUser"}],
        "userNotAllowedMessage": {"header": "No access", "text": "Ask an admin"},
    }), encoding="utf-8")
    settings = Settings(
        github_user_config_path=str(config_path),
        frontend_url="https://example.test/",
        encryption_secret=Fernet.generate_key().decode(),
    )
    user = User(github_user_id="42", username="AllowedUser", name="Allowed", avatar_url="")
    users = SimpleNamespace(
        upsert_from_github=AsyncMock(return_value=user),
        get_by_id=AsyncMock(return_value=user),
    )
    credentials = SimpleNamespace(upsert=AsyncMock())
    sessions = SimpleNamespace(
        create_session=AsyncMock(return_value="session-token"),
        resolve_session=AsyncMock(return_value=UserSession(user_id=user.id, token_hash="hash")),
        revoke_session=AsyncMock(),
    )
    token = OAuthToken(value="github-token", expires_at=utc_now() + timedelta(hours=1))
    exchange_token = AsyncMock(return_value=(token, token))
    monkeypatch.setattr(auth, "_exchange_code_for_token", exchange_token)
    github_user = AsyncMock(return_value={"id": 42, "login": "AllowedUser", "name": None})
    monkeypatch.setattr(auth, "get_github_user", github_user)

    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="test-secret")
    app.include_router(auth.router)
    app.include_router(work_items_router)
    app.include_router(public_work_items_router)
    app.include_router(metadata_router)
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_user_repository] = lambda: users
    app.dependency_overrides[get_github_credentials_repository] = lambda: credentials
    app.dependency_overrides[get_session_service] = lambda: sessions

    with TestClient(app) as client:
        yield SimpleNamespace(
            client=client, settings=settings, config_path=config_path,
            users=users, credentials=credentials, sessions=sessions,
            github_user=github_user, exchange_token=exchange_token,
        )


def _callback(client: TestClient):
    login_response = client.get("/auth/github/login", follow_redirects=False)
    state = parse_qs(urlsplit(login_response.headers["location"]).query)["state"][0]
    return client.get(
        "/auth/github/callback",
        params={"code": "github-code", "state": state},
        follow_redirects=False,
    )


def test_denied_login_redirects_without_storing_tokens_or_session(auth_setup):
    auth_setup.github_user.return_value["login"] = "NotAllowed"

    response = _callback(auth_setup.client)

    assert response.status_code == 303
    url = urlsplit(response.headers["location"])
    assert url.path == "/"
    assert parse_qs(url.query) == {"header": ["No access"], "text": ["Ask an admin"]}
    auth_setup.users.upsert_from_github.assert_not_awaited()
    auth_setup.credentials.upsert.assert_not_awaited()
    auth_setup.sessions.create_session.assert_not_awaited()
    assert auth_setup.client.get("/auth/github/me").status_code == 401


def test_allowed_login_and_removed_user_loses_existing_session(auth_setup):
    auth_setup.github_user.return_value["login"] = "alloweduser"

    response = _callback(auth_setup.client)

    assert response.status_code == 303
    assert response.headers["location"] == auth_setup.settings.frontend_url
    auth_setup.users.upsert_from_github.assert_awaited_once()
    auth_setup.credentials.upsert.assert_awaited_once()
    auth_setup.sessions.create_session.assert_awaited_once()
    assert auth_setup.client.get("/auth/github/me").status_code == 200

    auth_setup.config_path.write_text(json.dumps({
        "whiteList": [],
        "userNotAllowedMessage": {"header": "No access", "text": "Ask an admin"},
    }), encoding="utf-8")
    assert auth_setup.client.get("/auth/github/me").status_code == 403
    auth_setup.sessions.revoke_session.assert_awaited_once_with("session-token")
    assert auth_setup.client.get("/auth/github/me").status_code == 401


@pytest.mark.parametrize("path, method", [
    ("/v1/work-items/search?prompt=test", "get"),
    ("/v1/polarion-metadata/get-config", "get"),
    ("/v1/polarion-metadata/import-status", "get"),
])
def test_business_routes_require_login(auth_setup, path, method):
    response = getattr(auth_setup.client, method)(path)
    assert response.status_code == 401


def test_import_status_only_changes_after_successful_full_import(auth_setup, tmp_path):
    repository = SqliteImportStatusRepository(SQLiteDatabase(Settings(
        sqlite_file_path=str(tmp_path / "status.db"),
    )))
    app = auth_setup.client.app
    app.dependency_overrides[get_import_status_repository] = lambda: repository
    app.dependency_overrides[get_data_fetcher] = lambda: SimpleNamespace(fetch_data=Mock(return_value=iter(())))
    app.dependency_overrides[get_data_worker] = lambda: SimpleNamespace(work=Mock(return_value=3))
    ensure_indexes = Mock()
    app.dependency_overrides[get_work_item_service] = lambda: SimpleNamespace(ensure_indexes=ensure_indexes)

    status_path = "/v1/polarion-metadata/import-status"
    import_path = "/v1/work-items/ingest/import-polarion"
    assert auth_setup.client.post(import_path, params={"limit": 3}).status_code == 200
    assert auth_setup.client.get(status_path).status_code == 401
    assert _callback(auth_setup.client).status_code == 303
    assert auth_setup.client.get(status_path).json() is None

    assert auth_setup.client.post(import_path, params={"limit": 3}).status_code == 200
    assert auth_setup.client.get(status_path).json() is None

    assert auth_setup.client.post(import_path).status_code == 200
    saved = auth_setup.client.get(status_path).json()
    assert saved["collection_name"] == auth_setup.settings.qdrant_collection_name
    assert saved["processed_items"] == 3
    assert saved["completed_at"].endswith("Z")

    ensure_indexes.side_effect = RuntimeError("index failed")
    with pytest.raises(RuntimeError, match="index failed"):
        auth_setup.client.post(import_path)
    assert auth_setup.client.get(status_path).json() == saved


@pytest.mark.parametrize("config_path", [None, "missing", "invalid"])
def test_allowlist_configuration_failure_denies_login(auth_setup, config_path):
    if config_path == "missing":
        auth_setup.settings.github_user_config_path = str(
            auth_setup.config_path.parent / "absent.json"
        )
    elif config_path == "invalid":
        auth_setup.config_path.write_text('{"whiteList": "not a list"}', encoding="utf-8")
    else:
        auth_setup.settings.github_user_config_path = None

    response = _callback(auth_setup.client)

    assert response.status_code == 503
    auth_setup.exchange_token.assert_not_awaited()
    auth_setup.users.upsert_from_github.assert_not_awaited()
    auth_setup.credentials.upsert.assert_not_awaited()
    auth_setup.sessions.create_session.assert_not_awaited()