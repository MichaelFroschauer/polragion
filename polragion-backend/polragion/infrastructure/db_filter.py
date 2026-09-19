from dataclasses import dataclass, field
from enum import StrEnum


class FilterType(StrEnum):
    # When using must, the clause becomes true only if every condition listed inside must is satisfied.
    # In this sense, must is equivalent to the operator AND.
    MUST_MATCH = "Must Match"

    # Match Any works as a logical OR for the given values. It can also be described as a IN operator.
    MUST_MATCH_ANY = "Must Match Any"

@dataclass
class DbFilter:
    key: str
    value: str | list[str]
    filter_type: FilterType = field(default=FilterType.MUST_MATCH)
