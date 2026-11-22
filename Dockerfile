FROM python:3.14-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.13.6 /uv /bin/uv
WORKDIR /app
ENV UV_PYTHON_DOWNLOADS=never \
    UV_LINK_MODE=copy

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-dev --no-install-project
COPY src/ ./src/
RUN uv sync --locked --no-dev --no-editable

FROM python:3.14-slim AS runtime
WORKDIR /app
ENV UV_PYTHON_DOWNLOADS=never \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    REPORTES_FOTOS_DIR=/app/storage/reportes

RUN groupadd --gid 10001 app \
    && useradd --uid 10001 --gid app --create-home app \
    && (getent group 1000 >/dev/null || groupadd --gid 1000 render-secrets) \
    && usermod --append --groups 1000 app \
    && install -d -o app -g app /app/storage/reportes

COPY --from=builder /bin/uv /bin/uv
COPY --from=builder /app/.venv /app/.venv
COPY pyproject.toml uv.lock README.md ./

USER app
EXPOSE 10000
CMD ["sh", "-c", "exec uv run --no-sync uvicorn backend.main:app --host 0.0.0.0 --port \"${PORT:-10000}\""]
