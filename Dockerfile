FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 - # Устанавливаем Poetry

ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false

RUN poetry install --no-interaction --no-ansi

# Копирование исходного кода
COPY . .

EXPOSE 8000

# Запуск приложения
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]