import json
import logging
from typing import Collection, Any

from polragion.domain.vector_store import VectorDocument
from polragion.models.work_item import PolarionWorkItem, ReducedWorkItem, WorkItemSearchHit
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


def work_item_payload_to_reranker_text(work_item: dict[str, Any]) -> str:
    document_reranker_text: str = "\n".join([
        f"Document: {work_item.get("document_name")}",
        f"ID: {work_item.get("work_item_id")}",
        f"Type: {work_item.get("work_item_type")}",
        f"Title: {work_item.get("title")}",
        "",
        f"{work_item.get("description")}",
    ])
    return document_reranker_text


def work_item_search_hit_to_json_str(work_items: Collection[WorkItemSearchHit], *, reduced_information: bool = True) -> str:

    def _convert_work_item(work_item: PolarionWorkItem) -> PolarionWorkItem | ReducedWorkItem:
        if reduced_information:
            return ReducedWorkItem.from_work_item(work_item)
        else:
            return work_item

    retrieved_work_items = [
        {
            "retrieval_rank": index,
            "similarity_score": round(hit.score, 6),
            "id": str(f"{hit.work_item.project_id}:{hit.work_item.work_item_id}"),
            "work_item": _convert_work_item(hit.work_item).model_dump(
                mode="json",
                by_alias=True,
            ),
        }
        for index, hit in enumerate(work_items, start=1)
    ]

    context_json = json.dumps(
        retrieved_work_items,
        ensure_ascii=False,
        indent=2,
    )

    # Prevent work-item text from accidentally closing one of the XML sections.
    # These replacements keep the content valid JSON.
    context_json = (
        context_json
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
    )

    return context_json