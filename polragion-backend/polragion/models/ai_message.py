from uuid import UUID

from polragion.utils.general import StrictModel


class CopilotSendMessage(StrictModel):
    user_id: UUID
    text: str

class CopilotResponseMessage(StrictModel):
    text: str
    message_id: str | None = None
    is_final: bool = True

class CopilotMessageEvent(StrictModel):
    user_id: UUID
    message: CopilotResponseMessage
