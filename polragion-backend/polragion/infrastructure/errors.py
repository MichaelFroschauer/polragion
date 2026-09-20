class VectorStoreError(RuntimeError):
    """Base error raised by a vector store adapter."""


class VectorStoreUnavailableError(VectorStoreError):
    """The backing vector database cannot currently be reached."""


class VectorStoreConfigurationError(VectorStoreError):
    """Existing vector-store infrastructure is incompatible with the app."""


class ConfigurationError(Exception):
    """Base error raised by a configuration adapter."""
    def __init__(self, message: str, errors: list[dict] | None = None) -> None:
        super().__init__(message)
        self.errors = errors


class PolarionDataFetcherError(RuntimeError):
    """Base error raised by a data fetcher adapter."""