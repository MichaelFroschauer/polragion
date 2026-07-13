import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class QdrantConfig:
    client_connection: str = field(default_factory=lambda: os.getenv("QDRANT_URL", "http://localhost:6333"))
    collection_name: str = field(default_factory=lambda: os.getenv("QDRANT_COLLECTION_NAME", "polragion"))
    batch_size: int = field(default_factory=lambda: int(os.getenv("FASTEMBED_BATCH_SIZE", "256")))
    parallel: int = field(default_factory=lambda: int(os.getenv("FASTEMBED_PARALLEL", "4")))

@dataclass(frozen=True)
class FastEmbedConfig:
    model_name: str = field(default_factory=lambda: os.getenv("FASTEMBED_MODEL", "BAAI/bge-small-en-v1.5")) # "BAAI/bge-small-en"

@dataclass(frozen=True)
class VectorDBConfig:
    qdrant: QdrantConfig = field(default_factory=QdrantConfig)
    fastembed: FastEmbedConfig = field(default_factory=FastEmbedConfig)
