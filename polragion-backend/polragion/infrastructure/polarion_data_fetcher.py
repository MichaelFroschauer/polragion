from collections.abc import Iterable
from pathlib import Path
from typing import Any, Literal

import certifi
from polarion import polarion
from polarion.project import Project

from polragion.models.work_item import PolarionWorkItem, CustomFields, LinkedWorkItem
from polragion.settings import Settings
from polragion.utils.general import StrictModel
from pydantic import Field
from urllib.parse import unquote


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


class ProjectImportConfig(StrictModel):
    project_id: str
    enabled: bool = True
    documents: list[str]
    work_items: WorkItemImportConfig


class PolarionImportConfig(StrictModel):
    schema_version: int = 1
    projects: list[ProjectImportConfig]


def create_ca_bundle(company_ca_path: Path, output_path: Path) -> Path:

    certifi_bundle = Path(certifi.where()).read_bytes()
    company_bundle = company_ca_path.read_bytes()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(certifi_bundle.rstrip() + b"\n" + company_bundle.lstrip())

    return output_path.resolve()


_MISSING = object()

class PolarionDataFetcher:
    """
    Loads Polarion work items document by document.

    Results are buffered internally, but yielded individually as
    PolarionWorkItem objects.
    """

    _REQUIRED_FIELDS = (
        "id",
        "uri",
        "title",
        "type",
        "description",
        "status",
        "location",
        "linkedWorkItems",
        "linkedWorkItemsDerived",
    )

    def __init__(self, settings: Settings, import_config: PolarionImportConfig) -> None:

        if settings.max_ingest_batch_size <= 0:
            raise ValueError("max_ingest_batch_size must be greater than zero")

        self._batch_size = settings.max_ingest_batch_size
        self._import_config = import_config

        # ca_bundle = create_ca_bundle(
        #     company_ca_path=Path("certificates/company-ca.pem"),
        #     output_path=Path(".runtime/combined-ca-bundle.pem"),
        # )

        self._client = polarion.Polarion(
            polarion_url=settings.polarion_host,
            user=settings.polarion_user,
            password=settings.polarion_password,
            # verify_certificate=str(ca_bundle),
        )
        self._tracker_service = self._client.getService("Tracker")


    def fetch_data(self, limit: int | None = None) -> Iterable[PolarionWorkItem]:
        """
        Yield work items individually while buffering them internally
        in batches.

        The limit applies globally across projects and documents.
        Duplicate work items from different documents count separately.
        """

        if limit is not None and limit < 0:
            raise ValueError("limit must be greater than or equal to zero")

        if limit == 0:
            return

        fetched = 0

        for project_config in self._import_config.projects:
            if not project_config.enabled:
                continue

            if limit is not None and fetched >= limit:
                break

            polarion_project: Project = self._client.getProject(project_config.project_id)

            for document in project_config.documents:

                query = self._build_query(document=document, work_item_query=project_config.work_items.query)

                remaining = -1 if limit is None else limit - fetched

                requested_work_item_field_keys = self._requested_fields(project_config.work_items)
                requested_work_item_field_keys.remove("revision")
                requested_work_item_field_keys.remove("uri")

                raw_work_items = polarion_project.searchWorkitem(
                    query=query,
                    field_list=requested_work_item_field_keys,
                    limit=remaining,
                )

                batch: list[PolarionWorkItem] = []

                for raw_work_item in raw_work_items:
                    converted = self._convert_work_item(
                        raw_work_item=raw_work_item,
                        project_id=project_config.project_id,
                        project_name=polarion_project.name,
                    )
                    batch.append(converted)
                    fetched += 1

                    if len(batch) >= self._batch_size:
                        yield from batch
                        batch.clear()

                    if limit is not None and fetched >= limit:
                        break

                if batch:
                    yield from batch

                if limit is not None and fetched >= limit:
                    return


    def _convert_work_item(self, raw_work_item: Any, project_id: str, project_name: str | None) -> PolarionWorkItem:

        work_item_id = self._required_text(getattr(raw_work_item, "id", None), field_name="id")

        # work item type
        type_attr = getattr(raw_work_item, "type", None)
        type_value_id = self._required_text(value=self._enum_id(type_attr), field_name="type.id", work_item_id=work_item_id)
        type_value_name = self._to_text(self._enum_name(work_item_uri=raw_work_item.uri, field_key="type", enum_value=type_attr))
        work_item_type = type_value_name if type_value_name is not None and len(type_value_name) > 0 else type_value_id

        # work item status
        status_attr = getattr(raw_work_item, "status", None)
        status_value_id = self._enum_id(value=status_attr)
        status_value_name = self._enum_name(work_item_uri=raw_work_item.uri, field_key="status", enum_value=status_attr)
        work_item_status = status_value_name if status_value_name is not None and len(status_value_name) > 0 else status_value_id

        title: str | None = self._to_text(getattr(raw_work_item, "title", ""))
        uri = self._required_text(getattr(raw_work_item, "uri", None), field_name="uri", work_item_id=work_item_id)

        return PolarionWorkItem(
            project_id=project_id,
            project_name=project_name,
            document_name=self._get_document_name(raw_work_item=raw_work_item),
            work_item_id=work_item_id,
            work_item_type=work_item_type,
            title=title if title else "",
            description=self._text_value(getattr(raw_work_item, "description", None)),
            revision=self._get_revision(uri=uri, work_item_id=work_item_id),
            status=work_item_status,
            location=self._text_value(getattr(raw_work_item, "location", None)),
            linked_work_items=self._get_linked_work_items(raw_work_item=raw_work_item, source_work_item_id=work_item_id),
            custom_fields=CustomFields(
                safety_requirement=self._get_custom_field(
                    raw_work_item=raw_work_item,
                    key="safetyrequirement",
                )
            ),
        )


    def _get_revision(self, uri: str, work_item_id: str) -> int:

        try:
            revisions = self._tracker_service.getRevisions(uri)
        except Exception as exc:
            raise ValueError(f"Could not load revisions for work item {work_item_id!r}") from exc

        if not revisions:
            raise ValueError(f"No revisions returned for work item {work_item_id!r}")

        try:
            revision = int(revisions[-1])
        except (TypeError, ValueError, IndexError) as exc:
            raise ValueError(f"Invalid revision returned for work item {work_item_id!r}: {revisions!r}") from exc

        if revision < 1:
            raise ValueError(f"Revision for work item {work_item_id!r} must be at least 1, got {revision}")

        return revision


    def _get_linked_work_items(self, raw_work_item: Any, source_work_item_id: str) -> list[LinkedWorkItem]:

        linked_work_items: list[LinkedWorkItem] = []

        linked_work_items.extend(
            self._convert_links(
                container=getattr(raw_work_item, "linkedWorkItems", None),
                direction="outgoing",
                source_work_item_id=source_work_item_id,
            )
        )

        linked_work_items.extend(
            self._convert_links(
                container=getattr(raw_work_item, "linkedWorkItemsDerived", None),
                direction="incoming",
                source_work_item_id=source_work_item_id,
            )
        )

        return linked_work_items


    def _convert_links(self, container: Any, direction: Literal["outgoing", "incoming"], source_work_item_id: str) -> list[LinkedWorkItem]:

        if container is None:
            return []

        raw_links = getattr(container, "LinkedWorkItem", None)

        if raw_links is None:
            return []

        result: list[LinkedWorkItem] = []

        for raw_link in raw_links:
            role = self._enum_id(getattr(raw_link, "role", None))
            linked_uri = self._text_value(getattr(raw_link, "workItemURI", None))

            if role is None or linked_uri is None:
                continue

            try:
                linked_id = self._work_item_id_from_uri(linked_uri)
            except ValueError as exc:
                raise ValueError(f"Could not parse linked work-item URI {linked_uri!r} on work item {source_work_item_id!r}") from exc

            result.append(LinkedWorkItem(id=linked_id, role=role, direction=direction))

        return result


    def _get_custom_field(self, raw_work_item: Any, key: str) -> str | None:

        custom_fields = getattr(raw_work_item, "customFields", None)
        if custom_fields is None:
            return None

        raw_custom_fields = getattr(custom_fields, "Custom", None)
        if raw_custom_fields is None:
            return None

        for custom_field in raw_custom_fields:

            custom_field_key = getattr(custom_field, "key", None)
            if custom_field_key != key:
                continue

            return self._text_value(getattr(custom_field, "value", None))

        return None


    def _get_document_name(self, raw_work_item: Any) -> str:
        location = getattr(raw_work_item, "location", None)
        if (location is None or location.strip() == ""):
            return ""

        result = location.partition('/modules/')[2].partition('/workitems/')[0]
        return result


    @staticmethod
    def _enum_id(value: Any) -> str | None:
        if value is None:
            return None

        enum_id = getattr(value, "id", None)
        if enum_id is not None:
            return str(enum_id)

        return None

    def _enum_name(self, work_item_uri: str, field_key: str, enum_value: Any) -> str | None:
        if enum_value is None:
            return None

        enum_id = getattr(enum_value, "id", None)
        if not enum_id:
            return None

        option = self._tracker_service.getEnumOptionWithKey(work_item_uri, field_key, enum_value)

        if option is None:
            return None

        # TODO: Here could the icon been linked
        # option.properties.property[0].key = iconURL -> option.properties.property[0].value = '/polarion/icons/project/KeSafe_C5/system_Requirement.png'

        name = getattr(option, "name", None)
        return str(name) if name else str(enum_id)


    @staticmethod
    def _text_value(value: Any) -> str | None:
        """
        Convert normal strings and Polarion rich-text values into
        Python strings.
        """

        if value is None:
            return None

        if isinstance(value, str):
            return value

        content = getattr(value, "content", None)

        if content is not None:
            return str(content)

        enum_id = getattr(value, "id", None)

        if enum_id is not None:
            return str(enum_id)

        return str(value)


    @classmethod
    def _required_text(cls, value: Any, field_name: str, work_item_id: str | None = None) -> str:

        text = cls._to_text(value)

        if text is None or not text.strip():
            item_context = (f" for work item {work_item_id!r}" if work_item_id is not None else "")
            raise ValueError(f"Missing required Polarion field {field_name!r}{item_context}")

        return text


    @staticmethod
    def _work_item_id_from_uri(uri: str) -> str:
        """
        Extract the ID from a Polarion Subterra URI such as:

        subterra:data-service:objects:/default/project${WorkItem}ABC-123
        """

        decoded_uri = unquote(uri)
        marker = "${WorkItem}"

        if marker not in decoded_uri:
            raise ValueError(f"Unsupported Polarion work-item URI: {uri!r}")

        work_item_id = decoded_uri.rsplit(marker, maxsplit=1)[1]

        if not work_item_id:
            raise ValueError(
                f"Missing work-item ID in URI: {uri!r}"
            )

        return work_item_id


    @classmethod
    def _requested_fields(cls, config: WorkItemImportConfig) -> list[str]:
        fields = [
            *cls._REQUIRED_FIELDS,
            *config.requested_fields(),
        ]

        return list(dict.fromkeys(fields))


    @classmethod
    def _to_text(cls, value: Any) -> str | None:
        """
        Normalize common Polarion values.

        Handles strings as well as objects such as:
        - TextType(content=...)
        - EnumOptionId(id=...)
        """

        if value is None:
            return None

        if isinstance(value, str):
            return value

        if isinstance(value, bool):
            return "true" if value else "false"

        if isinstance(value, (int, float)):
            return str(value)

        content = cls._get_member(value, "content")

        if content is not None and content is not value:
            return cls._to_text(content)

        enum_id = cls._get_member(value, "id")

        if enum_id is not None and enum_id is not value:
            return cls._to_text(enum_id)

        return str(value)


    @staticmethod
    def _get_member(value: Any, name: str) -> Any:
        """
        Access both object attributes and dictionary entries.
        """

        if value is None:
            return None

        attribute = getattr(value, name, _MISSING)

        if attribute is not _MISSING:
            return attribute

        try:
            return value[name]
        except (KeyError, IndexError, TypeError):
            return None


    @staticmethod
    def _as_iterable(value: Any) -> tuple[Any, ...]:
        if value is None:
            return ()

        if isinstance(value, tuple):
            return value

        if isinstance(value, list):
            return tuple(value)

        if isinstance(value, (str, bytes)):
            return (value,)

        try:
            return tuple(value)
        except TypeError:
            return (value,)


    @classmethod
    def _build_field_list(cls, work_item_config: WorkItemImportConfig) -> list[str]:

        fields = [
            *cls._REQUIRED_FIELDS,
            *work_item_config.requested_fields(),
        ]

        return list(dict.fromkeys(fields))


    def _build_query(self, document: str, work_item_query: str | None) -> str:
        document_query = self._build_document_query([document])

        if work_item_query:
            return f"({document_query}) AND ({work_item_query})"

        return document_query


    @staticmethod
    def _build_document_query(
            documents: list[str],
    ) -> str:
        quoted_documents = [f"\"{doc}\"" for doc in documents]
        query = f"document.title:({" ".join(quoted_documents)})"
        return query

