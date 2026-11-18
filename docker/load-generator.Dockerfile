FROM python:3.13-slim

WORKDIR /app
RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
COPY src ./src

RUN uv sync --locked --no-build --no-dev

CMD ["uv", "run", "--no-sync", "python", "-m", "sre_agent.services.load_generator.main"]
