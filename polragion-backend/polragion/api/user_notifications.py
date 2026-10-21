import logging

from fastapi import Depends, APIRouter
from pydantic import BaseModel

from polragion.api.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/v1/notifications",
    tags=["notifications"],
    dependencies=[Depends(get_current_user)],
)

class UserNotification(BaseModel):
    id: str
    title: str
    description: str

class UserNotificationsResponse(BaseModel):
    notifications: list[UserNotification]

@router.get("", response_model=UserNotificationsResponse)
def get_user_notifications() -> UserNotificationsResponse:

    # TODO get these messages by reading them from a data source instead of set them here
    r = UserNotificationsResponse(
        notifications=[
            UserNotification(
                id="UN_1",
                title="Get Better Answers in ASK Mode",
                description=(
                    "For more consistent results, select a specific model "
                    "instead of Auto. Try GPT-6 Luna for simple questions "
                    "and GPT-6 Sol for more complex tasks."
                ),
            ),
            UserNotification(
                id="UN_2",
                title="MCP Server Support Is Here!",
                description=(
                    "PolRAGion now supports MCP servers! "
                    "Check out the documentation in Settings to get started."
                ),
            ),
        ]
    )
    return r
