# Use astral/uv slim Python image for both builder and runtime
ARG PYTHON_IMAGE=astral/uv:0.12.19-python3.13-trixie-slim@sha256:aba5f865793af9275ceaa06d30935dfc6db8b81969c9fb099b0ebca6396b189e

FROM ${PYTHON_IMAGE} AS builder
# Package directory name (e.g. 'app') — must be provided via --build-arg APP_NAME=my_package
ARG APP_NAME

# Compile Python bytecode on install for faster startup
# Copy instead of hardlink files (required for cache mounts)
# Use the system Python interpreter instead of downloading one
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /${APP_NAME}
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

COPY ./${APP_NAME} /${APP_NAME}/${APP_NAME}

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Shared runtime environment — 'local' and 'live' differ only by CMD
FROM ${PYTHON_IMAGE} AS base
# Package directory name (e.g. 'app') — must be provided via --build-arg APP_NAME=my_package
ARG APP_NAME
# Exported at runtime so start.sh can resolve the ASGI module path
ENV APP_NAME=${APP_NAME}

RUN apt-get update \
    && apt-get install --no-install-recommends -y ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy the application from the builder
COPY --from=builder /${APP_NAME} /${APP_NAME}
COPY ./scripts/start.sh /start.sh

RUN useradd appuser -m -s /bin/bash \
    && chown -R appuser:appuser /${APP_NAME} /start.sh \
    && chmod +x /start.sh

# Put the venv bin first on PATH so system python resolves to the app venv
ENV PATH="/${APP_NAME}/.venv/bin:$PATH" \
    # Make the app root importable from anywhere in the container
    PYTHONPATH=/${APP_NAME}

WORKDIR /${APP_NAME}
USER appuser

EXPOSE 8080

# `local` image used for development with hot reload
FROM base AS local
ENV ENVIRONMENT=local
CMD ["/start.sh", "--reload", "conf/logging.json"]

# `live` image used for runtime
FROM base AS live
ENV ENVIRONMENT=live
CMD ["/start.sh", "conf/logging.prod.json"]
