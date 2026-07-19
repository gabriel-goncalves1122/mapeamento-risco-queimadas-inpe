FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV DAGSTER_HOME=/opt/dagster/dagster_home \
    PYTHONPATH=/opt/dagster/app \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

WORKDIR /opt/dagster/app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY src ./src
RUN mkdir -p /opt/dagster/dagster_home

EXPOSE 3000

CMD ["uv", "run", "dagster", "dev", "-h", "0.0.0.0", "-p", "3000", "-m", "src.orchestration.repo"]
