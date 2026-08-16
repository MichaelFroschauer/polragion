import logging

from polragion.domain.vector_store import VectorDocument
from polragion.models.work_item import PolarionWorkItem
from polragion.utils.text_sanitizer import ParsedDocument, html_to_document

logger = logging.getLogger(__name__)

class WorkItemIndexMapper:
    """Maps domain work items to vector documents.

    Keeping embedding text construction outside the domain model makes it easy
    to version, replace, and test indexing strategies independently.
    """

    def to_document(self, work_item: PolarionWorkItem) -> VectorDocument:
        logical_id = f"{work_item.project_id}:{work_item.work_item_id}"

        description_text = work_item.description if work_item.description else ""
        document: ParsedDocument | None = html_to_document(description_text, remove_boilerplate=True)

        if document is None:
            logger.warning(f"Document with ID '{logical_id}' could not be html sanitized.")
            description_embedding_text = description_text
        else:
            work_item.description = document.markdown
            description_embedding_text = document.embedding_text

        dense_text = "\n".join([
            f"Title: {work_item.title}",
            "",
            description_embedding_text,
        ])

        sparse_text = "\n".join([
            f"Project: {work_item.project_id}",
            f"Document: {work_item.document_name}",
            f"ID: {work_item.work_item_id}",
            f"Type: {work_item.work_item_type}",
            f"Title: {work_item.title}",
            "",
            description_embedding_text,
        ])

        reranker_text = "\n".join([
            f"Document: {work_item.document_name}",
            f"ID: {work_item.work_item_id}",
            f"Type: {work_item.work_item_type}",
            f"Title: {work_item.title}",
            "",
            description_embedding_text,
        ])

        return VectorDocument(
            id=logical_id,
            dense_text=dense_text,
            sparse_text=sparse_text,
            reranker_text=reranker_text,
            metadata=work_item.model_dump(mode="json"),
        )
