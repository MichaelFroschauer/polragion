import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Iterator
from uuid import UUID

from polragion.database.repository import UserRepository, GitHubCredentialsRepository
from polragion.models.user import User, GitHubCredentials
from polragion.settings import Settings
from polragion.utils.general import utc_now


class SQLiteDatabase:

    def __init__(self, settings: Settings):
        self.settings = settings

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.settings.sqlite_file_path)
        conn.row_factory = sqlite3.Row
        return conn

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """Opens a connection, commits if succeeds otherwise rolls back and closes the connection."""
        conn = self._connect()
        try:
            with conn:
                yield conn
        finally:
            conn.close()

class SqliteUserRepository(UserRepository):

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.db = SQLiteDatabase(self.settings)
        self._create_schema()

    def _create_schema(self) -> None:
        with self.db.transaction() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id             TEXT PRIMARY KEY,
                    github_user_id TEXT NOT NULL UNIQUE,
                    username       TEXT NOT NULL,
                    created_at     TEXT NOT NULL
                )
                """
            )

    @staticmethod
    def _row_to_user(row: sqlite3.Row | None) -> User | None:
        if row is None:
            return None

        return User(
            id=UUID(row["id"]),
            github_user_id=row["github_user_id"],
            username=row["username"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    async def create(self, user: User) -> User:
        try:
            with self.db.transaction() as conn:
                conn.execute(
                    "INSERT INTO users (id, github_user_id, username, created_at) "
                    "VALUES (?, ?, ?, ?)",
                    (
                        str(user.id),
                        user.github_user_id,
                        user.username,
                        user.created_at.isoformat(),
                    ),
                )
        except sqlite3.Error as exc:
            raise ValueError(f"User could not be created: {exc}") from exc

        return user

    async def get_by_id(self, user_id: UUID) -> User | None:
        with self.db.transaction() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE id = ?",
                (str(user_id),),
            ).fetchone()

        return self._row_to_user(row)

    async def get_by_github_user_id(self, github_user_id: str) -> User | None:
        with self.db.transaction() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE github_user_id = ?",
                (github_user_id,)
            ).fetchone()

        return self._row_to_user(row)

    async def upsert_from_github(self, github_user_id: str, username: str) -> User:
        existing_user = await self.get_by_github_user_id(github_user_id)

        if existing_user is not None:
            updated_user = existing_user.model_copy(update={"username": username})

            with self.db.transaction() as conn:
                conn.execute(
                    "UPDATE users SET username = ? WHERE github_user_id = ?",
                    (username, github_user_id),
                )

            return updated_user

        new_user = User(github_user_id=github_user_id, username=username)

        return await self.create(new_user)


class SqliteGitHubCredentialsRepository(GitHubCredentialsRepository):

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.db = SQLiteDatabase(self.settings)
        self._create_schema()

    def _create_schema(self) -> None:
        with self.db.transaction() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS github_credentials(
                    user_id TEXT PRIMARY KEY,
                    access_token_encrypted TEXT NOT NULL,
                    access_token_expires_at TEXT NOT NULL,
                    refresh_token_encrypted TEXT NOT NULL,
                    refresh_token_expires_at TEXT NOT NULL,
                    updated_at TEXT
                )
                """
            )

    @staticmethod
    def _row_to_github_credentials(row: sqlite3.Row | None) -> GitHubCredentials | None:
        if row is None:
            return None

        return GitHubCredentials(
            user_id=UUID(row["user_id"]),
            access_token_encrypted=row["access_token_encrypted"],
            access_token_expires_at=datetime.fromisoformat(row["access_token_expires_at"]),
            refresh_token_encrypted=row["refresh_token_encrypted"],
            refresh_token_expires_at=datetime.fromisoformat(row["refresh_token_expires_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    async def create(self, credentials: GitHubCredentials) -> GitHubCredentials:
        try:
            with self.db.transaction() as conn:
                conn.execute(
                    "INSERT INTO github_credentials (user_id, access_token_encrypted, access_token_expires_at, refresh_token_encrypted, refresh_token_expires_at, updated_at)"
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        str(credentials.user_id),
                        credentials.access_token_encrypted,
                        credentials.access_token_expires_at.isoformat(),
                        credentials.refresh_token_encrypted,
                        credentials.refresh_token_expires_at.isoformat(),
                        credentials.updated_at.isoformat(),
                    )
                )
        except sqlite3.Error as exc:
            raise ValueError(f"GitHub credentials could not be created: {exc}") from exc

        return credentials

    async def get_by_id(self, user_id: UUID) -> GitHubCredentials | None:
        with self.db.transaction() as conn:
            row = conn.execute(
                "SELECT * FROM github_credentials WHERE user_id = ?",
                (str(user_id),)
            ).fetchone()

        return self._row_to_github_credentials(row)


    async def upsert(self, credentials: GitHubCredentials) -> GitHubCredentials:
        existing_credentials = await self.get_by_id(credentials.user_id)

        if existing_credentials is None:
            return await self.create(credentials)

        updated_credentials = existing_credentials.model_copy(
            update={
                "access_token_encrypted": credentials.access_token_encrypted,
                "access_token_expires_at": credentials.access_token_expires_at,
                "refresh_token_encrypted": credentials.refresh_token_encrypted,
                "refresh_token_expires_at": credentials.refresh_token_expires_at,
                "updated_at": utc_now()
            }
        )

        with self.db.transaction() as conn:
            conn.execute(
                """
                UPDATE github_credentials 
                SET access_token_encrypted = ?,
                    access_token_expires_at = ?,
                    refresh_token_encrypted = ?,
                    refresh_token_expires_at = ?,
                    updated_at = ?
                WHERE user_id = ?
                """,
                (
                    updated_credentials.access_token_encrypted,
                    updated_credentials.access_token_expires_at.isoformat(),
                    updated_credentials.refresh_token_encrypted,
                    updated_credentials.refresh_token_expires_at.isoformat(),
                    updated_credentials.updated_at.isoformat(),
                    str(updated_credentials.user_id),
                ),
            )

        return updated_credentials
