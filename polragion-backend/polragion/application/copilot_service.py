import time

import httpx
from copilot import CopilotClient, SessionEventType, PermissionHandler, RuntimeConnection

from polragion.settings import Settings


async def handle_oauth_callback(code: str, settings: Settings) -> str:

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={
                "Accept": "application/json",
            },
            json={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
            },
        )

        response.raise_for_status()
        data = response.json()

    if error := data.get("error"):
        description = data.get("error_description", "Unbekannter OAuth-Fehler")
        raise RuntimeError(f"GitHub OAuth fehlgeschlagen: {error}: {description}")

    access_token = data.get("access_token")

    if not access_token:
        raise RuntimeError(
            "GitHub hat keinen access_token zurückgegeben."
        )

    return access_token


class CopilotService:
    def __init__(self, settings: Settings) -> None:
        self.github_token = settings.github_fine_grained_token

        self.client = CopilotClient(
            mode="empty",
            connection=RuntimeConnection.for_uri(
                "localhost:4321",
                #connection_token=os.environ["COPILOT_CONNECTION_TOKEN"],
            ),
        )

    async def initialize(self) -> None:
        await self.client.start()

        user_id = "michael"

        session = await self.client.create_session(
            on_permission_request=PermissionHandler.approve_all,
            model="gpt-5.4",
            session_id=f"user-{user_id}-{int(time.time())}",
            github_token=self.github_token,
            available_tools=["custom:*"],
            #available_tools=ToolSet().add_builtin(BUILTIN_TOOLS_ISOLATED),
            streaming=True,
        )

        #session.resume_session()

        def handle_event(event) -> None:
            if event.type == SessionEventType.ASSISTANT_MESSAGE_DELTA:
                print(event.data.delta_content, end="", flush=True)
            elif event.type == SessionEventType.SESSION_IDLE:
                print()

        session.on(handle_event)

        #await session.send_and_wait("Tell me a short joke")



    async def shutdown(self) -> None:
        await self.client.stop()