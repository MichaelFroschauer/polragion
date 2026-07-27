# ============================================================================
# Build stage: install dependencies and the project into a .venv using uv
# ============================================================================
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS builder

# uv optimizations:
#   COMPILE_BYTECODE -> faster startup thanks to precompiled .pyc files
#   LINK_MODE=copy   -> avoids hardlink warnings across mount boundaries
#   PYTHON_DOWNLOADS=0 -> use the Python 3.14 already bundled in the image
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# 1) Install dependencies only without the project code (cachable).
#    pyproject.toml/uv.lock are only mounted, so they don't end up in the layer.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv sync --frozen --no-install-project --no-dev

# 2) Copy the project code (only what is needed) and install the project itself.
COPY pyproject.toml uv.lock README.md ./
COPY polragion ./polragion
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# ============================================================================
# Runtime stage: slim image without build tools
# ============================================================================
FROM python:3.14-slim-bookworm AS runtime

# curl is only needed for the container healthcheck.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Do not run as root. Use uid/gid 1000 so a bind-mounted data directory
# owned by the host user (typically 1000) stays writable.
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid 1000 --home-dir /app appuser

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Take the finished venv from the build stage + the application code.
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv
COPY --chown=appuser:appuser polragion ./polragion

# Writable data directory for the SQLite database (owned by the non-root user).
RUN mkdir -p /app/data && chown appuser:appuser /app/data

USER appuser

EXPOSE 8000

CMD ["uvicorn", "polragion.app:app", "--host", "0.0.0.0", "--port", "8000"]
