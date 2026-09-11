import logging
from datetime import datetime, UTC
from typing import TypeVar

from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)

def utc_now() -> datetime:
    return datetime.now(UTC)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")



T = TypeVar("T", bound=BaseModel)

def field_name(model: type[T], name: str) -> str:
    if name not in model.model_fields:
        logger.warning(f"{name!r} is not a field of {model.__name__}")
        raise ValueError(f"{name!r} is not a field of {model.__name__}")

    return name
