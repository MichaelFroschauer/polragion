from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Generic, TypeVar
from uuid import UUID

logger = logging.getLogger(__name__)

AiSendMessageT = TypeVar("AiSendMessageT")
AiResponseMessageT = TypeVar("AiResponseMessageT")
AiMessageEventT = TypeVar("AiMessageEventT")

MessageResponseHandler = Callable[[AiMessageEventT], None | Awaitable[None]]


class AiServiceError(RuntimeError):
    """Base exception for failures in an AI service."""


class AiService(ABC, Generic[AiSendMessageT, AiResponseMessageT, AiMessageEventT]):
    @abstractmethod
    async def initialize(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def send_message(self, message: AiSendMessageT) -> AiResponseMessageT:
        raise NotImplementedError

    @abstractmethod
    async def handle_message(self, message_event: AiMessageEventT) -> None:
        raise NotImplementedError

    @abstractmethod
    async def shutdown(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def add_message_response_handler(self, handler: MessageResponseHandler) -> Callable[[], None]:
        raise NotImplementedError

    @abstractmethod
    async def set_model_for_session(self, user_id: UUID, model_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_model_of_session(self, user_id: UUID) -> str:
        raise NotImplementedError

    @property
    def default_model_id(self) -> str:
        raise NotImplementedError