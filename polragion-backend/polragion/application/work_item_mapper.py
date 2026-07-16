from polragion.domain.vector_store import VectorDocument
from polragion.domain.work_item import PolarionWorkItem


class WorkItemIndexMapper:
    """Maps domain work items to vector documents.

    Keeping embedding text construction outside the domain model makes it easy
    to version, replace, and test indexing strategies independently.
    """

    def to_document(self, work_item: PolarionWorkItem) -> VectorDocument:
        logical_id = f"{work_item.project_id}:{work_item.workitem_id}"
        embedding_text = "\n".join(
            [
                f"Project: {work_item.project_id}",
                f"ID: {work_item.workitem_id}",
                f"Type: {work_item.custom_fields.workitem_type}",
                f"Status: {work_item.status}",
                f"Title: {work_item.title}",
                "",
                work_item.text,
            ]
        )

        return VectorDocument(
            id=logical_id,
            text=embedding_text,
            metadata=work_item.model_dump(mode="json"),
        )
