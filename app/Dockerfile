FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

EXPOSE 8080
WORKDIR /app

COPY . /app

RUN uv sync --locked

ENTRYPOINT ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]