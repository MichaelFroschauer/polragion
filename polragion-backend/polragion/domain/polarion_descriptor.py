from typing import Protocol


class PolarionDescriptor(Protocol):
    """Class interface for different kind of polarion descriptors"""

    def update_data(self) -> None:
        """Load information and other relevant attributes"""
        ...

    def get_project_ids(self) -> list[str]:
        ...

    def get_project_description(self, project_id: str) -> str | None:
        ...

    def get_project_context(self, project_id: str) -> list[str]:
        ...

    def get_documents(self, project_id: str) -> list[str]:
        ...
