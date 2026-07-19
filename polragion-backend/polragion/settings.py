import re
from functools import cached_property
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables or a .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Polragion Backend"
    log_level: str = "INFO"

    qdrant_url: str = "http://localhost:6333"
    qdrant_collection_prefix: str = "polragion"
    qdrant_batch_size: int = Field(default=256, ge=1, le=10_000)
    qdrant_parallel: int = Field(default=4, ge=1, le=64)

    fastembed_dense_model: str = "BAAI/bge-small-en-v1.5"
    #fastembed_dense_model: str = "BAAI/bge-large-en-v1.5"
    fastembed_sparse_model: str = "prithvida/Splade_PP_en_v1"
    fastembed_reranker_model: str = "BAAI/bge-reranker-base"
    qdrant_hybrid_candidate_limit: int = 50
    index_schema_version: int = Field(default=1, ge=1)

    search_default_limit: int = Field(default=5, ge=1, le=100)
    search_max_limit: int = Field(default=100, ge=1, le=1_000)
    search_score_threshold: float | None = Field(default=None, ge=0.0, le=1.0)

    max_ingest_batch_size: int = Field(default=2500, ge=1, le=50_000)

    json_data_source: str | Path = "/home/michael/gitclones/Polragion/testset/polarion_workitems_testset_2000_en/polarion_workitems_testset_2000_en.json"


    github_session_secret: str = ""
    github_client_id: str = ""
    github_client_secret: str = ""
    github_fine_grained_token: str = ""
    github_redirect_uri: str = ""

    @cached_property
    def qdrant_collection_name(self) -> str:
        """Return a model- and schema-versioned collection name.

        Embeddings from different models must never be mixed in one collection,
        even when both models happen to use the same vector dimension.
        """

        model_slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", self.fastembed_dense_model).strip("_")
        name = f"{self.qdrant_collection_prefix}_{model_slug}_schema_v{self.index_schema_version}"
        return name[:255]
