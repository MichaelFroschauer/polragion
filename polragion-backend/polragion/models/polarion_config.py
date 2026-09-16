from pathlib import Path

from pydantic import Field

from polragion.utils.general import StrictModel

def load_import_config(path: Path | str) -> PolarionImportConfig:

    if isinstance(path, str):
        path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    config_text = path.read_text(encoding="utf-8")
    return PolarionImportConfig.model_validate_json(config_text)


class RelationsConfig(StrictModel):
    fields: list[str] = Field(
        default_factory=lambda: [
            "linkedWorkItems",
            "linkedWorkItemsDerived",
        ]
    )


class WorkItemImportConfig(StrictModel):
    query: str | None = None

    common_fields: list[str]
    fields_by_type: dict[str, list[str]] = Field(default_factory=dict)
    relations: RelationsConfig = Field(default_factory=RelationsConfig)

    def requested_fields(self) -> list[str]:
        """Fields for all work items requested."""

        fields = list(self.common_fields)

        for type_fields in self.fields_by_type.values():
            fields.extend(type_fields)

        fields.extend(self.relations.fields)

        # Remove duplicates
        return list(dict.fromkeys(fields))

    def fields_for_type(self, work_item_type: str) -> list[str]:
        """Fields for a specific work item type."""

        fields = [
            *self.common_fields,
            *self.fields_by_type.get(work_item_type, []),
            *self.relations.fields,
        ]

        return list(dict.fromkeys(fields))


class ProjectDocument(StrictModel):
    name: str
    category: str
    language: str
    description: str


class ProjectImportConfig(StrictModel):
    project_id: str
    enabled: bool = True
    description: str
    project_context: str
    documents: list[ProjectDocument]
    work_items: WorkItemImportConfig


class PolarionImportConfig(StrictModel):
    schema_version: int = 1
    projects: list[ProjectImportConfig]

    def get_project_by_id(self, project_id: str) -> ProjectImportConfig | None:
        for project in self.projects:
            if project.project_id == project_id:
                return project
        return None
