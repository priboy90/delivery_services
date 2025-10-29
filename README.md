# 🚀 Delivery Services API

Микросервис для международной службы доставки.
Реализован на **FastAPI**, с асинхронной обработкой, очередями **RabbitMQ**, кешированием через **Redis** и хранением данных в **PostgreSQL**.
Аналитика логов расчётов доставок сохраняется в **MongoDB**.

---

## 📦 Основной функционал

- 📮 Регистрация посылок (через REST API, с RabbitMQ-процессингом)
- 🧾 Список посылок пользователя (по сессии, с пагинацией и фильтрами)
- 💰 Автоматический расчёт стоимости доставки
- 🏷️ Привязка посылки к транспортной компании (атомарно, «первый победил»)
- 🔄 Асинхронные операции, логирование, кэширование курса USD→RUB
- 📊 Хранение истории расчётов в MongoDB и аналитика по типам

---

## 🛠️ Технологический стек

- **FastAPI**, **SQLAlchemy 2.0**, **Pydantic v2**
- **PostgreSQL** — основное хранилище данных
- **Redis** — кеш курса валют
- **RabbitMQ** — очередь регистрации посылок
- **MongoDB** — аналитика расчётов
- **Alembic** — миграции БД
- **Docker Compose** — инфраструктура и запуск
- **Pytest** — автотесты

---

## 🚀 Быстрый старт

### 1️⃣ Подготовка

Скопируй пример переменных окружения и при необходимости измени:

```bash
cp .env.example .env
```

---

### 2️⃣ Сборка и запуск

Собери и запусти сервис вместе с воркером и зависимостями:

```bash
docker compose up -d --build app worker
```

Проверить статус контейнеров:

```bash
docker compose ps
```

---

### 3️⃣ Открыть API

- Swagger UI → [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc → [http://localhost:8000/redoc](http://localhost:8000/redoc)
- Healthcheck → [http://localhost:8000/health](http://localhost:8000/health)

---

## 🧪 Тестирование

Прогнать все тесты:

```bash
docker compose build tests
docker compose run --rm tests
```

Если всё успешно — появится:

```
============================= 7 passed in XXs =============================
```

---

## 🧩 Структура проекта

```
src/
 ├── app/
 │   ├── api/           # Роуты FastAPI
 │   ├── models/        # SQLAlchemy модели
 │   ├── services/      # Redis, RabbitMQ, расчёт стоимости и т.п.
 │   ├── middleware/    # Сессионный middleware
 │   ├── db/            # Инициализация PostgreSQL
 │   └── main.py        # Точка входа приложения
 ├── alembic/           # Миграции
 └── tests/             # Автотесты Pytest
```

---

## ⚙️ Полезные команды

Остановить сервисы:
```bash
docker compose down
```

Полностью очистить контейнеры и данные:
```bash
docker compose down -v
```

Просмотреть логи:
```bash
docker compose logs -f app
docker compose logs -f worker
```

---
