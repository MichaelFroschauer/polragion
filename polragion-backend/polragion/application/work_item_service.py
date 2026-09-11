from collections.abc import Iterable

from polragion.application.work_item_mapper import WorkItemIndexMapper
from polragion.domain.vector_store import VectorStore
from polragion.infrastructure.db_filter import DbFilter, FilterType
from polragion.models.work_item import PolarionWorkItem, WorkItemSearchHit
from polragion.utils.general import field_name


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
        work_item_id: str | None = None,
        score_threshold: float | None = None,
        **kwargs
    ) -> list[WorkItemSearchHit]:

        exact_search = False
        db_filters: list[DbFilter] = []

        project_id = project_id.strip() if project_id else None
        work_item_id = work_item_id.strip() if work_item_id else None

        if project_id and work_item_id:
            db_filters.append(DbFilter(key="_polragion_document_id", value=f"{project_id}:{work_item_id}", filter_type=FilterType.MUST_MATCH))
            query = "Query will be ignored..."
            exact_search = True
        elif project_id:
            db_filters.append(DbFilter(key=field_name(PolarionWorkItem, "project_id"), value=project_id, filter_type=FilterType.MUST_MATCH))
            exact_search = False
        elif work_item_id:
            db_filters.append(DbFilter(key=field_name(PolarionWorkItem, "work_item_id"), value=work_item_id, filter_type=FilterType.MUST_MATCH))
            query = "Query will be ignored..."
            exact_search = True

        hits = self._vector_store.search(
            query,
            limit=limit,
            db_filters=db_filters,
            exact_search=exact_search,
            score_threshold=score_threshold,
            **kwargs
        )

        return [
            WorkItemSearchHit(
                work_item=PolarionWorkItem.model_validate(hit.metadata),
                score=hit.score,
                point_id=hit.point_id,
            )
            for hit in hits
        ]
