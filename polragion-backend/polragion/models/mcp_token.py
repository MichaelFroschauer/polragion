"""Personal MCP credential records and safe API metadata."""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import Field

from polragion.utils.general import StrictModel, utc_now


class McpTokenInfo(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    name: str
    created_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime
    revoked_at: datetime | None = None


class McpToken(McpTokenInfo):
    token_hash: str
