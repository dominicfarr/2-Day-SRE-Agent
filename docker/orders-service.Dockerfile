FROM python:3.13-slim

ARG SERVICE_VERSION=v1
ENV SERVICE_VERSION=${SERVICE_VERSION}

WORKDIR /app
RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
COPY src ./src

RUN uv sync --locked --no-build --no-dev

EXPOSE 8000
CMD ["uv", "run", "--no-sync", "uvicorn", "sre_agent.services.orders_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
