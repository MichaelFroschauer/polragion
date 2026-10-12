# PolRAGion backend

FastAPI backend for Polarion ingestion, Qdrant retrieval, GitHub authentication, and Copilot conversations.

See the [project README](../README.md), [setup guide](../doc/setup.md), and [architecture notes](ARCHITECTURE.md). Current configuration defaults are in [settings.py](polragion/settings.py); Python requirements are in [pyproject.toml](pyproject.toml).

From this directory, run `uv sync --extra dev` to install dependencies and `uv run pytest` for tests. Enable `DEBUG=true` for Swagger API documentation in development.
