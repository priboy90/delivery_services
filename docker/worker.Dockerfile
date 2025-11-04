FROM python:3.12-slim AS lint

WORKDIR /src
RUN pip install --no-cache-dir ruff pre-commit
COPY .pre-commit-config.yaml pyproject.toml poetry.lock ./
COPY src src
COPY tests tests
RUN ruff check . && pre-commit run --all-files --show-diff-on-failure

FROM python:3.12-slim
ENV POETRY_VIRTUALENVS_CREATE=false \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl gcc libpq-dev \
 && rm -rf /var/lib/apt/lists/*
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:${PATH}"
COPY pyproject.toml ./
RUN poetry install --no-interaction --no-ansi --no-root
COPY ./src ./src
COPY docker/worker.entrypoint.sh /usr/local/bin/worker-entrypoint.sh
RUN chmod +x /usr/local/bin/worker-entrypoint.sh
VOLUME ["/var/log/worker"]
ENTRYPOINT ["/usr/local/bin/worker-entrypoint.sh"]
CMD ["python", "-m", "src.app.workers.consumer"]
