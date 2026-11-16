from dataclasses import dataclass

from polragion.models.search_filters import DocumentSelection, WorkItemFilters
from polragion.models.work_item import PolarionWorkItem


@dataclass(frozen=True, slots=True)
class SearchScope:
    """Vector search restrictions that apply to every search within one AI request.

    Lives in its own module so ``copilot_tools`` can import it without creating a
    cycle with ``user_request_manager``.
    """

    project_ids: tuple[str, ...] = ()
    project_contexts: tuple[str, ...] = ()
    document_categories: tuple[str, ...] = ()

    documents: tuple[DocumentSelection, ...] = ()
    match_none: bool = False

    @classmethod
    def from_filters(cls, filters: WorkItemFilters | None) -> "SearchScope":
        if filters is None:
            return cls()
        return cls.create(
            project_ids=filters.project_ids,
            project_contexts=filters.project_contexts,
            document_categories=filters.document_categories,
            documents=filters.documents,
        )

    @classmethod
    def create(
        cls,
        project_ids: list[str] | None = None,
        project_contexts: list[str] | None = None,
        document_categories: list[str] | None = None,
        documents: list[DocumentSelection] | None = None,
    ) -> "SearchScope":
        return cls(
            project_ids=_clean(project_ids),
            project_contexts=_clean(project_contexts),
            document_categories=_clean(document_categories),
            documents=tuple(dict.fromkeys(documents or [])),
            match_none=any(
                values is not None and not _clean(values)
                for values in (project_ids, project_contexts, document_categories)
            )
            or documents == [],
        )

    def is_empty(self) -> bool:
        return not (
            self.match_none
            or self.project_ids
            or self.project_contexts
            or self.document_categories
            or self.documents
        )

    def allows(self, work_item: PolarionWorkItem) -> bool:
        """Check an already fetched work item, used where filtering cannot happen in the query."""

        if self.match_none:
            return False

        if self.documents and not any(
            doc.project_id == work_item.project_id and doc.document_name == work_item.document_name
            for doc in self.documents
        ):
            return False

        if self.project_ids and work_item.project_id not in self.project_ids:
            return False

        if self.project_contexts and not set(work_item.project_context).intersection(
            self.project_contexts
        ):
            return False

        return (
            not self.document_categories or work_item.document_category in self.document_categories
        )


def _clean(values: list[str] | None) -> tuple[str, ...]:
    if not values:
        return ()

    return tuple(dict.fromkeys(value.strip() for value in values if value and value.strip()))
