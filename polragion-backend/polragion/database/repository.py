from abc import ABC, abstractmethod
from typing import TypeVar, Generic
from uuid import UUID

from polragion.models.user import GitHubCredentials, UserSession, User

EntityT = TypeVar("EntityT")
EntityIdT = TypeVar("EntityIdT")

class Repository(ABC, Generic[EntityT, EntityIdT]):

    @abstractmethod
    async def create(self, entity: EntityT) -> EntityT:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, entity_id: EntityIdT) -> EntityT | None:
        raise NotImplementedError


class UserRepository(Repository[User, UUID], ABC):

    @abstractmethod
    async def get_by_github_user_id(self, github_user_id: str) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def upsert_from_github(self, github_user_id: str, username: str) -> User:
        raise NotImplementedError


class GitHubCredentialsRepository(Repository[GitHubCredentials, UUID], ABC):

    @abstractmethod
    async def upsert(self, credentials: GitHubCredentials) -> GitHubCredentials:
        raise NotImplementedError


class SessionRepository(Repository[UserSession, UUID], ABC):

    @abstractmethod
    async def get_by_token_hash(self, token_hash: str) -> UserSession | None:
        raise NotImplementedError

    @abstractmethod
    async def revoke(self, session_id: UUID) -> None:
        raise NotImplementedError
