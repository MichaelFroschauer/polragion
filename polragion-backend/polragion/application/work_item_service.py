from collections.abc import Iterable

from polragion.application.search_scope import SearchScope
from polragion.application.work_item_mapper import WorkItemIndexMapper
from polragion.domain.vector_store import VectorDocument, VectorStore
from polragion.infrastructure.db_filter import DbFilter, DbFilterAny, FilterType
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
        documents: list[VectorDocument] = [self._mapper.to_document(item) for item in work_items]
        self._vector_store.upsert(documents)
        return len(documents)

    def ensure_indexes(self) -> None:
        self._vector_store.ensure_payload_indexes(self._mapper.filterable_payload_keys())

    def search(
        self,
        query: str,
        *,
        limit: int,
        project_id: str | None = None,
        work_item_id: str | None = None,
        score_threshold: float | None = None,
        scope: SearchScope | None = None,
        **kwargs,
    ) -> list[WorkItemSearchHit]:

        scope = scope or SearchScope()
        if scope.match_none:
            return []
        exact_search = False
        db_filters: list[DbFilter | DbFilterAny] = []

        project_id = project_id.strip() if project_id else None
        work_item_id = work_item_id.strip() if work_item_id else None

        if project_id and work_item_id:
            db_filters.append(
                DbFilter(
                    key="_polragion_document_id",
                    value=f"{project_id}:{work_item_id}",
                    filter_type=FilterType.MUST_MATCH,
                )
            )
            query = "Query will be ignored..."
            exact_search = True
        elif project_id:
            db_filters.append(
                DbFilter(
                    key=field_name(PolarionWorkItem, "project_id"),
                    value=project_id,
                    filter_type=FilterType.MUST_MATCH,
                )
            )
            exact_search = False
        elif work_item_id:
            db_filters.append(
                DbFilter(
                    key=field_name(PolarionWorkItem, "work_item_id"),
                    value=work_item_id,
                    filter_type=FilterType.MUST_MATCH,
                )
            )
            query = "Query will be ignored..."
            exact_search = True
        # User scope and tool-supplied restrictions are independent AND conditions.
        for key, values in (
            ("project_id", scope.project_ids),
            ("project_context", scope.project_contexts),
            ("document_category", scope.document_categories),
        ):
            if values:
                db_filters.append(
                    DbFilter(key=key, value=list(values), filter_type=FilterType.MUST_MATCH_ANY)
                )
        if scope.documents:
            db_filters.append(
                DbFilterAny(
                    branches=[
                        [
                            DbFilter(key="project_id", value=doc.project_id),
                            DbFilter(key="document_name", value=doc.document_name),
                        ]
                        for doc in scope.documents
                    ]
                )
            )

        hits = self._vector_store.search(
            query,
            limit=limit,
            db_filters=db_filters,
            exact_search=exact_search,
            score_threshold=score_threshold,
            **kwargs,
        )

        return [
            WorkItemSearchHit(
                work_item=PolarionWorkItem.model_validate(hit.metadata),
                score=hit.score,
                point_id=hit.point_id,
            )
            for hit in hits
        ]
