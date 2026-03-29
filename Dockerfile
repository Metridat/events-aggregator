FROM python:3.11-slim

RUN addgroup --system --gid 1000 appuser && \
    adduser --system --uid 1000 --ingroup appuser appuser

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini .

RUN chown -R appuser:appuser /app

USER appuser

ENV UV_CACHE_DIR=/tmp/uv-cache

CMD ["sh", "-c", "/app/.venv/bin/alembic upgrade head && /app/.venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000"]