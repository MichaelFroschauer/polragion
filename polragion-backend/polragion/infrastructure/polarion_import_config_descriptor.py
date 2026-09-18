from pathlib import Path

from polragion.models.polarion_config import PolarionImportConfig, load_import_config, ProjectImportConfig
from polragion.settings import Settings


class PolarionImportConfigDescriptor:
    """Class interface for different kind of polarion descriptors"""

    def __init__(self, settings: Settings, import_config_path: str | Path) -> None:
        self._settings = settings
        self._import_config_path = import_config_path
        self._import_config = load_import_config(import_config_path)


    def update_data(self) -> None:
        """Load information and other relevant attributes"""
        self._import_config = load_import_config(self._import_config_path)


    def get_project_ids(self) -> list[str]:
        project_ids: list[str] = [
            project.project_id
            for project in self._import_config.projects
            if project.project_id is not None
        ]
        return project_ids


    def get_project_description(self, project_id: str) -> str | None:
        return self._get_project_by_id(project_id).description


    def get_project_context(self, project_id: str) -> list[str]:
        return self._get_project_by_id(project_id).project_context


    def get_documents(self, project_id: str) -> list[str]:
        documents = self._get_project_by_id(project_id).documents
        doc_names = [doc.name for doc in documents if doc is not None]
        return doc_names


    def _get_project_by_id(self, project_id: str) -> ProjectImportConfig | None:
        for project in self._import_config.projects:
            if project.project_id == project_id:
                return project
        return None
