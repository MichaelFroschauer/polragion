from uuid import UUID

from polragion.database.repository import UserRepository, GitHubCredentialsRepository, SessionRepository
from polragion.models.user import User, GitHubCredentials, UserSession
from polragion.utils.general import utc_now


class InMemoryUserRepository(UserRepository):

    def __init__(self) -> None:
        self._users: dict[UUID, User] = {}
        self._users_by_github_id: dict[str, UUID] = {}

    async def create(self, user: User) -> User:
        if user.id in self._users:
            raise ValueError(f"User with ID {user.id} already exists")

        if user.github_user_id in self._users_by_github_id:
            raise ValueError("GitHub user is already connected")

        self._users[user.id] = user
        self._users_by_github_id[user.github_user_id] = user.id

        return user

    async def get_by_id(self, user_id: UUID) -> User | None:
        return self._users.get(user_id)

    async def get_by_github_user_id(self, github_user_id: str) -> User | None:
        user_id = self._users_by_github_id.get(github_user_id)

        if user_id is None:
            return None

        return self._users.get(user_id)

    async def upsert_from_github(self, github_user_id: str, username: str) -> User:
        existing_user = await self.get_by_github_user_id(github_user_id)

        if existing_user is not None:
            updated_user = existing_user.model_copy(
                update={"username": username}
            )

            self._users[existing_user.id] = updated_user
            return updated_user

        new_user = User(
            github_user_id=github_user_id,
            username=username,
        )

        return await self.create(new_user)


class InMemoryGitHubCredentialsRepository(GitHubCredentialsRepository):

    def __init__(self) -> None:
        self._credentials: dict[UUID, GitHubCredentials] = {}

    async def create(self, credentials: GitHubCredentials) -> GitHubCredentials:
        if credentials.user_id in self._credentials:
            raise ValueError("Credentials already exist for this user")

        self._credentials[credentials.user_id] = credentials
        return credentials

    async def get_by_id(self, user_id: UUID) -> GitHubCredentials | None:
        return self._credentials.get(user_id)

    async def upsert(self, credentials: GitHubCredentials) -> GitHubCredentials:
        updated_credentials = credentials.model_copy(
            update={"updated_at": utc_now()}
        )

        self._credentials[credentials.user_id] = updated_credentials

        return updated_credentials


class InMemorySessionRepository(SessionRepository):

    def __init__(self) -> None:
        self._sessions: dict[UUID, UserSession] = {}
        self._sessions_by_token_hash: dict[str, UUID] = {}

    async def create(self, session: UserSession) -> UserSession:
        if session.id in self._sessions:
            raise ValueError(f"Session with ID {session.id} already exists")

        if session.token_hash in self._sessions_by_token_hash:
            raise ValueError("Session token already exists")

        self._sessions[session.id] = session
        self._sessions_by_token_hash[session.token_hash] = session.id

        return session

    async def get_by_id(self, session_id: UUID) -> UserSession | None:
        return self._sessions.get(session_id)

    async def get_by_token_hash(self, token_hash: str) -> UserSession | None:
        session_id = self._sessions_by_token_hash.get(token_hash)

        if session_id is None:
            return None

        return self._sessions.get(session_id)

    async def revoke(self, session_id: UUID) -> None:
        session = self._sessions.get(session_id)

        if session is None:
            return

        self._sessions[session_id] = session.model_copy(
            update={"revoked_at": utc_now()}
        )
