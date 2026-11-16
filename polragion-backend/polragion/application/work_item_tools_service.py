"""Tool use cases shared by MCP and Copilot, without either SDK or request state."""

import json

from polragion.application.search_scope import SearchScope
from polragion.application.work_item_mapper import work_item_search_hit_to_json_str
from polragion.application.work_item_service import WorkItemService
from polragion.domain.polarion_descriptor import PolarionDescriptor
from polragion.models.tool_parameters import LookupWorkItemsParams, SearchWorkItemsParams
from polragion.models.work_item import WorkItemSearchHit
from polragion.settings import Settings


class WorkItemToolsService:
    def __init__(
        self,
        settings: Settings,
        work_item_service: WorkItemService,
        polarion_descriptor: PolarionDescriptor,
    ):
        self.settings = settings
        self.work_item_service = work_item_service
        self.polarion_descriptor = polarion_descriptor

    def search(
        self, params: SearchWorkItemsParams, scope: SearchScope | None = None
    ) -> list[WorkItemSearchHit]:
        scope = scope or SearchScope()
        if not params.search_text.strip():
            raise ValueError("Search text must not be blank")
        project_id = params.polarion_project_id
        if project_id is not None and not project_id.strip():
            raise ValueError("Project ID must not be blank")
        project_id = project_id.strip() if project_id else None
        if project_id and scope.project_ids and project_id not in scope.project_ids:
            raise ValueError(f"Project '{project_id}' is not available in this request.")
        threshold = params.search_score_threshold
        if threshold is None:
            threshold = self.settings.search_score_threshold
        return self.work_item_service.search(
            params.search_text,
            limit=min(
                params.search_limit or self.settings.search_default_limit,
                self.settings.search_max_limit,
            ),
            score_threshold=threshold if threshold is not None else 0.0,
            project_id=project_id,
            scope=scope,
            do_reranking=False,
        )

    def lookup(
        self, params: LookupWorkItemsParams, scope: SearchScope | None = None
    ) -> list[WorkItemSearchHit]:
        if not params.polarion_work_item_id.strip():
            raise ValueError("Work item ID must not be blank")
        if params.polarion_project_id is not None and not params.polarion_project_id.strip():
            raise ValueError("Project ID must not be blank")
        return self.work_item_service.search(
            "",
            limit=1,
            score_threshold=0.0,
            project_id=params.polarion_project_id,
            work_item_id=params.polarion_work_item_id,
            scope=scope,
        )

    @staticmethod
    def format_results(results: list[WorkItemSearchHit], reduced: bool) -> str:
        return work_item_search_hit_to_json_str(results, reduced_information=reduced)

    def projects(self, scope: SearchScope | None = None) -> str:
        descriptor = self.polarion_descriptor
        scope = scope or SearchScope()
        return json.dumps(
            [
                {
                    "project_id": project_id,
                    "project_description": descriptor.get_project_description(project_id) or "",
                    "project_context": descriptor.get_project_context(project_id),
                }
                for project_id in descriptor.get_project_ids()
                if self._project_available(project_id, scope)
            ]
        )

    def documents(self, project_id: str | None, scope: SearchScope | None = None) -> str:
        descriptor = self.polarion_descriptor
        if project_id is not None and not project_id.strip():
            raise ValueError("Project ID must not be blank")
        scope = scope or SearchScope()
        project_ids = [project_id] if project_id else descriptor.get_project_ids()
        return json.dumps(
            [
                {
                    "project_id": pid,
                    "project_context": descriptor.get_project_context(pid),
                    "documents": [
                        name
                        for name in descriptor.get_documents(pid)
                        if self._document_available(pid, name, scope)
                    ],
                }
                for pid in project_ids
                if self._project_available(pid, scope)
            ]
        )

    def _project_available(self, project_id: str, scope: SearchScope) -> bool:
        if scope.match_none or (scope.project_ids and project_id not in scope.project_ids):
            return False
        if scope.project_contexts and not set(scope.project_contexts).intersection(
            self.polarion_descriptor.get_project_context(project_id)
        ):
            return False
        if scope.documents or scope.document_categories:
            return any(
                self._document_available(project_id, name, scope)
                for name in self.polarion_descriptor.get_documents(project_id)
            )
        return True

    def _document_available(self, project_id: str, name: str, scope: SearchScope) -> bool:
        if scope.documents and not any(
            doc.project_id == project_id and doc.document_name == name for doc in scope.documents
        ):
            return False
        return (
            not scope.document_categories
            or self.polarion_descriptor.get_document_category(project_id, name)
            in scope.document_categories
        )
