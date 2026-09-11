from dataclasses import dataclass, field
from enum import StrEnum


class FilterType(StrEnum):
    MUST_MATCH = "Must Match"

@dataclass
class DbFilter:
    key: str
    value: str
    filter_type: FilterType = field(default=FilterType.MUST_MATCH)
