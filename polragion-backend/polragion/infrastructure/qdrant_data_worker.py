import logging
from collections.abc import Iterable

from polragion.application.work_item_service import WorkItemService
from polragion.models.work_item import PolarionWorkItem
from polragion.settings import Settings
from polragion.utils.general import html_to_markdown

logger = logging.getLogger(__name__)

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
            logger.info("Fetched work item with ID: %s", work_item.work_item_id)

            work_item.description = html_to_markdown(work_item.description)

            batch.append(work_item)

            if len(batch) >= self._batch_size:
                work_count += self._work_item_service.ingest(batch)
                batch.clear()

        if batch:
            work_count += self._work_item_service.ingest(batch)

        return work_count
