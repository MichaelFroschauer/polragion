from collections.abc import Iterable
from dataclasses import dataclass

from polragion.application.work_item_mapper import WorkItemIndexMapper
from polragion.domain.vector_store import VectorStore
from polragion.domain.work_item import PolarionWorkItem


@dataclass(frozen=True, slots=True)
class WorkItemSearchResult:
    work_item: PolarionWorkItem
    score: float
    point_id: str


class WorkItemService:
    def __init__(
        self,
        vector_store: VectorStore,
        mapper: WorkItemIndexMapper,
    ) -> None:
        self._vector_store = vector_store
        self._mapper = mapper

    def ingest(self, work_items: Iterable[PolarionWorkItem]) -> int:
        documents = [self._mapper.to_document(item) for item in work_items]
        self._vector_store.upsert(documents)
        return len(documents)

    def search(
        self,
        query: str,
        *,
        limit: int,
        project_id: str | None = None,
        score_threshold: float | None = None,
    ) -> list[WorkItemSearchResult]:
        hits = self._vector_store.search(
            query,
            limit=limit,
            project_id=project_id,
            score_threshold=score_threshold,
        )

        return [
            WorkItemSearchResult(
                work_item=PolarionWorkItem.model_validate(hit.metadata),
                score=hit.score,
                point_id=hit.point_id,
            )
            for hit in hits
        ]
