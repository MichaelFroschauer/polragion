class VectorStoreError(RuntimeError):
    """Base error raised by a vector store adapter."""


class VectorStoreUnavailableError(VectorStoreError):
    """The backing vector database cannot currently be reached."""


class VectorStoreConfigurationError(VectorStoreError):
    """Existing vector-store infrastructure is incompatible with the app."""
