# src/main.py
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from starlette.middleware.sessions import SessionMiddleware

from .core.settings import settings
from .core.database import engine
from .core.session import get_session_config
from .routers import packages

from .models.models import Users
from .dependencies import Depends, get_current_user



# Настройка логирования
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s' if settings.LOG_FORMAT == "console" else None
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager для асинхронного приложения"""
    # Startup
    logging.info(f"Starting {settings.APP_NAME} in {settings.ENVIRONMENT} mode")

    # Проверяем подключение к БД
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logging.info("Соединение с базой данных установлено")
    except Exception as e:
        logging.error(f"Не удалось подключиться к базе данных: {e}")
        raise

    yield

    # Shutdown
    await engine.dispose()
    logging.info("Соединение с базой данных закрыто")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    docs_url=settings.DOCS_URL if settings.DEBUG else None,
    redoc_url=settings.REDOC_URL if settings.DEBUG else None,
    lifespan=lifespan,
)


# Добавляем middleware для сессий
app.add_middleware(SessionMiddleware, **get_session_config())

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




# подключаем роуты
app.include_router(packages.router)

@app.get("/")
async def test_user(current_user: Users = Depends(get_current_user)):
    """Тестовый эндпоинт для проверки пользователя"""
    return {
        "user_id": str(current_user.id),
        "session_id": current_user.session_id,
        "created_at": current_user.created_at.isoformat(),
        "last_activity": current_user.last_activity.isoformat()
    }


@app.get("routers/v1/health/db")
async def db_health_check():
    """Проверка здоровья базы данных"""
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            return {"database": "connected"}
    except Exception as e:
        return {"database": "disconnected", "error": str(e)}
