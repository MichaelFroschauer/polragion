from __future__ import annotations

import asyncio
import inspect
import logging
from collections.abc import Callable
from datetime import datetime, timedelta
from uuid import UUID, uuid4

import httpx
from copilot import CopilotClient, RuntimeConnection
from copilot.session import CopilotSession, PermissionHandler
from copilot.session_events import (
    AssistantMessageData,
    AssistantMessageDeltaData,
    SessionErrorData,
    SessionEvent,
)
from cryptography.fernet import InvalidToken

from polragion.application.ai_service import AiServiceError, AiService, MessageResponseHandler
from polragion.database.repository import GitHubCredentialsRepository
from polragion.models.ai_message import (
    CopilotMessageEvent,
    CopilotResponseMessage,
    CopilotSendMessage,
)
from polragion.settings import Settings
from polragion.utils.general import utc_now
from polragion.utils.token_cipher import TokenCipher

logger = logging.getLogger(__name__)

class GitHubCredentialsMissingError(AiServiceError):
    """The user has no stored GitHub credentials."""


class GitHubReauthenticationRequiredError(AiServiceError):
    """The GitHub credentials can no longer be refreshed."""


class GitHubTokenRefreshError(AiServiceError):
    """GitHub rejected or failed the token refresh request."""


class CopilotRequestError(AiServiceError):
    """A request to the Copilot runtime failed."""

class CopilotService(AiService[CopilotSendMessage, CopilotResponseMessage, CopilotMessageEvent]):
    TOKEN_EXPIRY_SKEW = timedelta(minutes=5)
    REQUEST_TIMEOUT_SECONDS = 120.0

    def __init__(
            self,
            settings: Settings,
            github_credentials_repository: GitHubCredentialsRepository,
            *,
            runtime_url: str = "localhost:4321",
            runtime_connection_token: str | None = None,
            model: str = "gpt-5.4",
    ) -> None:
        self.settings = settings
        self.credentials_repository = github_credentials_repository
        self.model = model

        self.user_sessions: dict[UUID, CopilotSession] = {}
        self._session_token_expirations: dict[UUID, datetime | None] = {}
        self._user_locks: dict[UUID, asyncio.Lock] = {}
        self._lifecycle_lock = asyncio.Lock()
        self._initialized = False
        self._event_tasks: set[asyncio.Task[None]] = set()

        self.message_response_handlers: list[MessageResponseHandler] = []

        self.client = CopilotClient(
            mode="empty",
            connection=RuntimeConnection.for_uri(
                runtime_url,
                connection_token=runtime_connection_token,
            ),
        )


    async def initialize(self) -> None:
        async with self._lifecycle_lock:
            if self._initialized:
                return

            await self.client.start()
            self._initialized = True
            logger.info("Copilot client started")


    def add_message_response_handler(self, handler: MessageResponseHandler) -> Callable[[], None]:
        """Register a sync or async response handler and return an unsubscribe callback."""
        self.message_response_handlers.append(handler)

        def unsubscribe() -> None:
            try:
                self.message_response_handlers.remove(handler)
            except ValueError:
                pass

        return unsubscribe


    async def _get_valid_access_token(self, user_id: UUID) -> tuple[str, datetime | None]:
        credentials = await self.credentials_repository.get_by_id(user_id)

        if credentials is None or not credentials.access_token_encrypted:
            raise GitHubCredentialsMissingError(f"No GitHub credentials are stored for user {user_id}")

        token_cipher = TokenCipher(self.settings.encryption_secret)
        now = utc_now()
        access_expires_at = credentials.access_token_expires_at

        # A missing expiry can represent a non-expiring OAuth token.
        if access_expires_at is None or access_expires_at > now + self.TOKEN_EXPIRY_SKEW:
            try:
                return token_cipher.decrypt(credentials.access_token_encrypted), access_expires_at
            except (InvalidToken, ValueError) as exc:
                raise GitHubReauthenticationRequiredError("The stored GitHub access token cannot be decrypted") from exc

        if not credentials.refresh_token_encrypted:
            raise GitHubReauthenticationRequiredError("The GitHub access token expired and no refresh token is stored")

        refresh_expires_at = credentials.refresh_token_expires_at
        if refresh_expires_at is not None and refresh_expires_at <= now:
            raise GitHubReauthenticationRequiredError("The GitHub refresh token has expired")

        try:
            refresh_token = token_cipher.decrypt(credentials.refresh_token_encrypted)
        except (InvalidToken, ValueError) as exc:
            raise GitHubReauthenticationRequiredError("The stored GitHub refresh token cannot be decrypted") from exc

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    "https://github.com/login/oauth/access_token",
                    headers={"Accept": "application/json"},
                    data={
                        "client_id": self.settings.github_client_id,
                        "client_secret": self.settings.github_client_secret,
                        "grant_type": "refresh_token",
                        "refresh_token": refresh_token,
                    },
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error("GitHub token refresh returned HTTP %s: %s", exc.response.status_code, exc.response.text)
            raise GitHubTokenRefreshError("GitHub rejected the token refresh request") from exc
        except httpx.RequestError as exc:
            raise GitHubTokenRefreshError("GitHub could not be reached while refreshing the token") from exc

        try:
            data = response.json()
        except ValueError as exc:
            logger.error("Invalid GitHub token response: %s", response.text)
            raise GitHubTokenRefreshError("GitHub returned an invalid token response") from exc

        if error := data.get("error"):
            description = data.get("error_description", "Unknown GitHub OAuth error")
            if error == "bad_refresh_token":
                raise GitHubReauthenticationRequiredError(f"GitHub reauthentication is required: {description}")
            raise GitHubTokenRefreshError(f"{error}: {description}")

        access_token = data.get("access_token")
        access_expires_in = data.get("expires_in")
        new_refresh_token = data.get("refresh_token")
        refresh_expires_in = data.get("refresh_token_expires_in")

        if not isinstance(access_token, str) or not access_token:
            raise GitHubTokenRefreshError("GitHub did not return a new access token")
        if not isinstance(access_expires_in, int) or isinstance(access_expires_in, bool) or access_expires_in <= 0:
            raise GitHubTokenRefreshError("GitHub did not return a valid access-token lifetime")
        if not isinstance(new_refresh_token, str) or not new_refresh_token:
            raise GitHubTokenRefreshError("GitHub did not return a new refresh token")
        if not isinstance(refresh_expires_in, int) or isinstance(refresh_expires_in, bool) or refresh_expires_in <= 0:
            raise GitHubTokenRefreshError("GitHub did not return a valid refresh-token lifetime")

        refreshed_at = utc_now()
        new_access_expires_at = refreshed_at + timedelta(seconds=access_expires_in)
        new_refresh_expires_at = refreshed_at + timedelta(seconds=refresh_expires_in)

        # GitHub rotates both tokens. Persist both before returning the access token.
        updated_credentials = credentials.model_copy(
            update={
                "access_token_encrypted": token_cipher.encrypt(access_token),
                "access_token_expires_at": new_access_expires_at,
                "refresh_token_encrypted": token_cipher.encrypt(new_refresh_token),
                "refresh_token_expires_at": new_refresh_expires_at,
            }
        )
        await self.credentials_repository.upsert(updated_credentials)

        logger.info("Refreshed GitHub credentials for user %s", user_id)
        return access_token, new_access_expires_at


    async def _create_user_session(self, user_id: UUID) -> CopilotSession:
        access_token, access_token_expires_at = (await self._get_valid_access_token(user_id))

        try:
            session = await self.client.create_session(
                on_permission_request=PermissionHandler.approve_all,
                model=self.model,
                session_id=f"user-{user_id}-{uuid4()}",
                github_token=access_token,
                available_tools=["custom:*"],
                streaming=True,
            )
        except Exception as exc:
            raise CopilotRequestError(f"Could not create a Copilot session for user {user_id}") from exc

        def on_event(event: SessionEvent) -> None:
            message_event: CopilotMessageEvent | None = None

            match event.data:
                case AssistantMessageDeltaData() as data:
                    if data.delta_content:
                        message_event = CopilotMessageEvent(
                            user_id=user_id,
                            message=CopilotResponseMessage(
                                text=data.delta_content,
                                message_id=data.message_id,
                                is_final=False,
                            ),
                        )
                case AssistantMessageData() as data:
                    message_event = CopilotMessageEvent(
                        user_id=user_id,
                        message=CopilotResponseMessage(
                            text=data.content,
                            message_id=data.message_id,
                            is_final=True,
                        ),
                    )
                case SessionErrorData() as data:
                    logger.error("Copilot session error for user %s: type=%s code=%s message=%s",
                                 user_id,
                                 data.error_type,
                                 data.error_code,
                                 data.message,
                                 )

            if message_event is None:
                return

            task = asyncio.create_task(self.handle_message(message_event))
            self._event_tasks.add(task)
            task.add_done_callback(self._event_task_finished)

        session.on(on_event)
        self.user_sessions[user_id] = session
        self._session_token_expirations[user_id] = access_token_expires_at

        logger.info("Created Copilot session for user %s", user_id)
        return session


    def _event_task_finished(self, task: asyncio.Task[None]) -> None:
        self._event_tasks.discard(task)
        if task.cancelled():
            return

        exception = task.exception()
        if exception is not None:
            logger.error(
                "Unhandled Copilot event-handler error",
                exc_info=(
                    type(exception),
                    exception,
                    exception.__traceback__,
                ),
            )


    async def _disconnect_user_session(self, user_id: UUID) -> None:
        session = self.user_sessions.pop(user_id, None)
        self._session_token_expirations.pop(user_id, None)

        if session is None:
            return

        try:
            await session.disconnect()
        except Exception:
            logger.exception("Could not disconnect Copilot session for user %s", user_id)

    async def _get_user_session(self, user_id: UUID) -> CopilotSession | None:
        session = self.user_sessions.get(user_id)
        if session is None:
            return None

        token_expires_at = self._session_token_expirations.get(user_id)
        if token_expires_at is not None and token_expires_at <= utc_now() + self.TOKEN_EXPIRY_SKEW:
            await self._disconnect_user_session(user_id)
            return None

        return session


    async def close_user_session(self, user_id: UUID) -> None:
        lock = self._user_locks.setdefault(user_id, asyncio.Lock())
        async with lock:
            await self._disconnect_user_session(user_id)


    async def send_message(self, message: CopilotSendMessage) -> CopilotResponseMessage:
        if not message.text.strip():
            raise ValueError("message.text must not be empty")

        await self.initialize()

        # Serialize messages per user. This also prevents duplicate session/token refreshes.
        lock = self._user_locks.setdefault(message.user_id, asyncio.Lock())
        async with lock:
            session = await self._get_user_session(message.user_id)
            if session is None:
                session = await self._create_user_session(message.user_id)

            try:
                response_event = await session.send_and_wait(message.text, timeout=self.REQUEST_TIMEOUT_SECONDS)
            except TimeoutError as exc:
                await self._disconnect_user_session(message.user_id)
                raise CopilotRequestError("Copilot did not finish the response before the timeout") from exc
            except Exception as exc:
                # Recreate the possibly broken session on the next request.
                await self._disconnect_user_session(message.user_id)
                raise CopilotRequestError("The Copilot request failed") from exc

        if response_event is None:
            raise CopilotRequestError("Copilot finished without returning an assistant message")

        match response_event.data:
            case AssistantMessageData() as data:
                return CopilotResponseMessage(text=data.content, message_id=data.message_id, is_final=True)
            case _:
                raise CopilotRequestError("Copilot returned an unexpected response event")


    async def handle_message(self, message_event: CopilotMessageEvent) -> None:
        # Work on a copy so handlers may unsubscribe while events are dispatched.
        for response_handler in tuple(self.message_response_handlers):
            try:
                result = response_handler(message_event)
                if inspect.isawaitable(result):
                    await result
            except Exception:
                logger.exception("Copilot response handler failed for user %s", message_event.user_id)


    async def shutdown(self) -> None:
        async with self._lifecycle_lock:
            if not self._initialized:
                return

            sessions = list(self.user_sessions.items())
            self.user_sessions.clear()
            self._session_token_expirations.clear()
            self._user_locks.clear()

            results = await asyncio.gather(*(session.disconnect() for _, session in sessions), return_exceptions=True)
            for (user_id, _), result in zip(sessions, results, strict=True):
                if isinstance(result, BaseException):
                    logger.error("Could not disconnect Copilot session for user %s: %s", user_id, result)

            for task in self._event_tasks:
                task.cancel()
            if self._event_tasks:
                await asyncio.gather(*self._event_tasks, return_exceptions=True)
            self._event_tasks.clear()

            try:
                await self.client.stop()
            finally:
                self._initialized = False

            logger.info("Copilot client stopped")
