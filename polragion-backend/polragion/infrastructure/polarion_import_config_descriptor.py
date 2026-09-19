from pathlib import Path

from polragion.models.polarion_config import PolarionImportConfig, load_import_config, ProjectImportConfig
from polragion.settings import Settings


class PolarionImportConfigDescriptor:
    """Class interface for different kind of polarion descriptors"""

    def __init__(self, settings: Settings, import_config_path: str | Path) -> None:
        self._settings = settings
        self._import_config_path = import_config_path
        self._import_config = load_import_config(import_config_path)

        self._project_ids = []
        self._project_categories = []
        self._project_contexts = []
        self._load_data()


    def update_data(self) -> None:
        """Load information and other relevant attributes"""
        self._import_config = load_import_config(self._import_config_path)
        self._load_data()


    def get_project_ids(self) -> list[str]:
        return self._project_ids


    def get_project_categories(self) -> list[str]:
        return self._project_categories


    def get_project_contexts(self) -> list[str]:
        return self._project_contexts


    def get_project_description(self, project_id: str) -> str | None:
        return self._get_project_by_id(project_id).description


    def get_project_context(self, project_id: str) -> list[str]:
        return self._get_project_by_id(project_id).project_context


    def get_documents(self, project_id: str) -> list[str]:
        documents = self._get_project_by_id(project_id).documents
        doc_names = [doc.name for doc in documents if doc is not None]
        return doc_names


    def get_document_category(self, project_id: str, document_name: str) -> str | None:
        documents = self._get_project_by_id(project_id).documents
        for doc in documents:
            if doc.name == document_name:
                return doc.category
        return None


    def _get_project_by_id(self, project_id: str) -> ProjectImportConfig | None:
        for project in self._import_config.projects:
            if project.project_id == project_id:
                return project
        return None


    def _load_data(self):
        self._project_ids = [
            project.project_id
            for project in self._import_config.projects
            if project.project_id is not None
        ]

        self._project_categories = list(dict.fromkeys(
            document.category
            for project in self._import_config.projects
            for document in project.documents
        ))

        self._project_contexts = list(dict.fromkeys(
            context
            for project in self._import_config.projects
            for context in project.project_context
        ))
