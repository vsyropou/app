ARG PYTHON_IMAGE=astral/uv:0.12.19-python3.13-trixie-slim

FROM ${PYTHON_IMAGE}

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

COPY requirements.toml ./requirements.toml
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Model package and optional extra paths from the build context
COPY ./model.py /app/model/
COPY ./model/schemas.py /app/model/

COPY ../api/schemas.py /app/api
COPY ../vectorstore/schemas.py /app/vectorstore
COPY ../interfaces.py /app/
COPY ../runner.py /app/
COPY ../tracking app/