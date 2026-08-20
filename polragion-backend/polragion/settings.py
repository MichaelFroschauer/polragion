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

    # =======================================================================
    #   Application Config
    app_name: str = "Polragion Backend"
    log_level: str = "INFO"
    debug: bool = False

    # =======================================================================
    #   Frontend Config
    frontend_url: str = "https://localhost:5173/"

    # =======================================================================
    #   Copilot CLI Config
    copilot_url: str = "localhost:4321"

    # =======================================================================
    #   Sqlite Config
    sqlite_file_path: str = ""

    # =======================================================================
    #   Qdrant Config
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection_prefix: str = "polragion"
    qdrant_batch_size: int = Field(default=32, ge=1, le=10_000)
    qdrant_upload_parallel: int = Field(default=4, ge=1, le=64)
    qdrant_client_timeout_seconds: int = Field(default=120, ge=1, le=3600)

    #   FastEmbed Simple Embedding Config
    #   https://qdrant.github.io/fastembed/examples/Supported_Models/#supported-text-embedding-models
    # fastembed_dense_model: str = "BAAI/bge-small-en-v1.5"

    #   FastEmbed Hybrid Embedding Config (Dense + Sparse Embedding Hybrid Search)
    fastembed_dense_model: str = "BAAI/bge-base-en"
    fastembed_sparse_model: str = "prithivida/Splade_PP_en_v1"
    fastembed_reranker_model: str = "jinaai/jina-reranker-v1-turbo-en"
    fastembed_reranker_batch_size: int = Field(default=32, ge=1, le=10_000)

    fastembed_cache_path: str = ""
    fastembed_parallel: int | None = Field(default=None, ge=1, le=64)

    qdrant_hybrid_candidate_limit: int = Field(default=50, ge=1, le=50_000)

    #   Other different vector DB configurations
    index_schema_version: int = Field(default=1, ge=1)
    search_default_limit: int = Field(default=50, ge=1, le=100)
    search_max_limit: int = Field(default=200, ge=1, le=1_000)
    search_score_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    max_ingest_batch_size: int = Field(default=100, ge=1, le=50_000)

    json_data_source: str | Path = ""


    # =======================================================================
    #   Security Config
    session_secret: str = ""
    encryption_secret: str = ""
    # The session cookie may only carry the Secure flag when the backend is
    # actually reachable over HTTPS, otherwise the browser discards it.
    session_cookie_secure: bool = True

    #=======================================================================
    #   GitHub Config
    github_client_id: str = ""
    github_client_secret: str = ""
    github_fine_grained_token: str = ""
    github_redirect_uri: str = ""

    # =======================================================================
    #   Polarion Config
    polarion_host: str = ""
    polarion_user: str = ""
    polarion_password: str = ""
    polarion_import_config_path: str = ""
    # Path to the Polarion server's CA certificate (PEM). When set, it is merged
    # with the certifi bundle at runtime.
    polarion_ca_cert_path: str = ""


    @cached_property
    def qdrant_collection_name(self) -> str:

        model_slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", self.fastembed_dense_model).strip("_")
        name = f"{self.qdrant_collection_prefix}_{model_slug}_schema_v{self.index_schema_version}"
        return name[:255]
