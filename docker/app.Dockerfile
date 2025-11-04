FROM python:3.12-slim

ENV POETRY_VIRTUALENVS_CREATE=false \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

COPY pyproject.toml ./pyproject.toml
RUN poetry install --no-interaction --no-ansi --no-root

COPY ./src ./src

COPY docker/app.entrypoint.sh /usr/local/bin/app-entrypoint.sh
RUN chmod +x /usr/local/bin/app-entrypoint.sh

VOLUME ["/var/log/app"]
EXPOSE 8000
ENTRYPOINT ["/usr/local/bin/app-entrypoint.sh"]
