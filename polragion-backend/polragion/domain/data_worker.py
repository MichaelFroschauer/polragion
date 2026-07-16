from collections.abc import Iterable
from typing import Protocol

from polragion.domain.work_item import PolarionWorkItem


class DataWorker(Protocol):

    def work(self, data_list: Iterable[PolarionWorkItem]) -> int:
        """Works through a list of PolarionWorkItems."""
        ...