import uuid
from typing import Final

from fastembed import TextEmbedding
from fastembed.common.model_description import ModelSource, PoolingType

_POINT_NAMESPACE = uuid.UUID("8604873a-0779-49ef-81c4-840c4567d718")
_DOCUMENT_ID_PAYLOAD_KEY = "_polragion_document_id"
_RESERVED_PAYLOAD_KEYS = {
    _DOCUMENT_ID_PAYLOAD_KEY,
}

JINA_DE_FP32_MODEL_NAME: Final = "jinaai/jina-embeddings-v2-base-de-fp32"


def register_custom_fastembed_models() -> None:
    """Register embedding models that FastEmbed does not ship in a usable form.

    FastEmbed hardcodes ORT_ENABLE_ALL, and that optimization level crashes onnxruntime 1.27
    on the fp16 graph of jinaai/jina-embeddings-v2-base-de, so the fp32 export is used instead.
    """

    if any(model["model"] == JINA_DE_FP32_MODEL_NAME for model in TextEmbedding.list_supported_models()):
        return

    TextEmbedding.add_custom_model(
        model=JINA_DE_FP32_MODEL_NAME,
        pooling=PoolingType.MEAN,
        normalization=True,
        sources=ModelSource(hf="jinaai/jina-embeddings-v2-base-de"),
        dim=768,
        model_file="onnx/model.onnx",
        description=(
            "Text embeddings, Unimodal (text), Multilingual (German, English), "
            "8192 input tokens truncation, fp32 export of jinaai/jina-embeddings-v2-base-de."
        ),
        license="apache-2.0",
        size_in_gb=0.64,
    )

def qdrant_point_id(logical_id: str) -> str:
    """Create a deterministic UUID accepted by Qdrant."""

    return str(uuid.uuid5(_POINT_NAMESPACE, logical_id))
