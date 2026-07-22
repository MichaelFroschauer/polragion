from collections.abc import Iterable

from polragion.models.work_item import PolarionWorkItem


class PolarionDataFetcher:

    def fetch_data(self, limit: int | None = None) -> Iterable[PolarionWorkItem]:
        if limit is not None and limit < 0:
            raise ValueError("limit must be greater than or equal to zero")

        if limit == 0:
            return

        fetched = 0
        while limit is None or fetched < limit:
            item = self._fetch_next_item()

            if item is None:
                return

            yield item
            fetched += 1

    def _fetch_next_item(self) -> PolarionWorkItem | None:
        ...