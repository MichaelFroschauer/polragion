from collections.abc import Iterable
from typing import Protocol

from polragion.domain.work_item import PolarionWorkItem


class DataFetcher(Protocol):

    def fetch_data(self, limit: int | None = None) -> Iterable[PolarionWorkItem]:
        """Fetches a list of PolarionWorkItems from a data source."""
        ...
