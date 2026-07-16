from collections.abc import Iterable

from polragion.application.work_item_service import WorkItemService
from polragion.domain.work_item import PolarionWorkItem
from polragion.settings import Settings


class QdrantDataWorker:

    def __init__(self, settings: Settings, work_item_service: WorkItemService, *, batch_size: int = 100) -> None:
        if batch_size <= 0:
            raise ValueError("batch_size must be greater than zero")

        self._settings = settings
        self._work_item_service = work_item_service
        self._batch_size = batch_size

    def work(self, data_list: Iterable[PolarionWorkItem]) -> int:
        work_count = 0
        batch: list[PolarionWorkItem] = []

        for work_item in data_list:
            batch.append(work_item)

            if len(batch) >= self._batch_size:
                work_count += self._work_item_service.ingest(batch)
                batch.clear()

        if batch:
            work_count += self._work_item_service.ingest(batch)

        return work_count
