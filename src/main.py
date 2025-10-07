# src/main.py
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from .core.settings import settings
from .core.database import engine

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

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "message": f"Добро пожаловать в {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "debug": settings.DEBUG,
        "environment": settings.ENVIRONMENT
    }


@app.get("/api/v1/health/db")
async def db_health_check():
    """Проверка здоровья базы данных"""
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            return {"database": "connected"}
    except Exception as e:
        return {"database": "disconnected", "error": str(e)}
