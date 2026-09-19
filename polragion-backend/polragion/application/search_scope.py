from dataclasses import dataclass

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

    @classmethod
    def create(
        cls,
        project_ids: list[str] | None = None,
        project_contexts: list[str] | None = None,
        document_categories: list[str] | None = None,
    ) -> "SearchScope":
        return cls(
            project_ids=_clean(project_ids),
            project_contexts=_clean(project_contexts),
            document_categories=_clean(document_categories),
        )

    def is_empty(self) -> bool:
        return not (self.project_ids or self.project_contexts or self.document_categories)

    def allows(self, work_item: PolarionWorkItem) -> bool:
        """Check an already fetched work item, used where filtering cannot happen in the query."""

        if self.project_ids and work_item.project_id not in self.project_ids:
            return False

        if self.project_contexts and not set(work_item.project_context) & set(self.project_contexts):
            return False

        if self.document_categories and work_item.document_category not in self.document_categories:
            return False

        return True


def _clean(values: list[str] | None) -> tuple[str, ...]:
    if not values:
        return ()

    return tuple(dict.fromkeys(value.strip() for value in values if value and value.strip()))
