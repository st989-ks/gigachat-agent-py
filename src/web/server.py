"""
GigaChat Agent Web Server - FastAPI приложение

Полная интеграция с системой агентов и инструментов.
Поддерживает:
- Управление сессиями с паролями
- История диалогов
- Интеграция с агентами (Main, Manager, Custom)
- Система инструментов (Tools)
- Расширенная логирование
"""

from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime
import uuid
import logging
import os

# Импорты из проекта
from src.gigachat_client.client import GigaChatClient
from src.gigachat_client.catalog_agents import get_catalog
from src.session.session_manager import get_session_manager
from src.config.constants import DEFAULT_AGENT_TEMPERATURE, LOG_FORMAT

# ===== Конфигурация логирования =====
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Приложение запускается...")
    print_startup_info()
    yield
    logger.info("🛑 Приложение выключается...")


# ===== Инициализация FastAPI приложения =====
app = FastAPI(
    title="GigaChat Agent",
    lifespan=lifespan,
    description="Веб-интерфейс для работы с GigaChat API через многоагентную архитектуру",
    version="2.0.0",
)

# ===== CORS конфигурация =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== Подключение статических файлов =====
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")
    logger.info("✅ Статические файлы подключены")
else:
    logger.warning("⚠️ Папка static не найдена")

# ===== Инициализация компонентов системы =====
try:
    gigachat_client = GigaChatClient()
    logger.info("✅ GigaChat клиент инициализирован")
except Exception as e:
    logger.error(f"❌ Ошибка при инициализации GigaChat клиента: {e}")
    raise

try:
    agent_catalog = get_catalog()
    session_manager = get_session_manager()
    logger.info("✅ Система агентов и сессий инициализирована")
except Exception as e:
    logger.error(f"❌ Ошибка при инициализации системы агентов: {e}")
    raise


# ===== Модели данных для API =====

class Auth(BaseModel):
    password: str


class ErrorResp(BaseModel):
    error: str
    message: str


class QuestionResponse(BaseModel):
    history: Optional[List[Dict[str, str]]] = None


class Question(BaseModel):
    question: str
    password: str


class ModelConfig(BaseModel):
    """Конфигурация модели."""
    temperature: float = DEFAULT_AGENT_TEMPERATURE
    user_prompt: Optional[str] = None
    agent_key: Optional[str] = None

    response_format: Optional[Dict[str, str]] = None


def get_time_now() -> str:
    return datetime.now().strftime("%H:%M")


# ===== HTTP эндпоинты =====

@app.get("/", response_class=HTMLResponse)
async def root():
    """Редирект на страницу чата."""
    return HTMLResponse("""
        <html>
            <head>
                <meta http-equiv="refresh" content="0; url=/chat" />
            </head>
            <body>
                <p>Перенаправление на <a href="/chat">страницу чата</a>...</p>
            </body>
        </html>
    """)


@app.get("/chat", response_class=HTMLResponse)
async def chat_page():
    """
    Возвращает HTML страницу чата.

    GET /chat -> HTML интерфейс чата
    """
    try:
        with open(f"static/index.html", encoding="utf-8") as f:
            logger.info("📄 Страница чата загружена")
            return HTMLResponse(f.read())
    except FileNotFoundError:
        logger.error("❌ Файл index.html не найден")
        return HTMLResponse(
            "<h1>404: Страница не найдена</h1><p>Файл static/index.html отсутствует</p>",
            status_code=404
        )


@app.post("/api/verify")
async def verify(request: Request, auth: Auth):
    password = auth.password.strip()

    logger.info(f"📥 Запрос авторизации")

    # Проверка пароля
    if not password:
        logger.warning("⚠️ Пустой пароль")
        return JSONResponse(
            {
                "error": "empty_password",
                "message": "Введи пароль"
            },
            status_code=400
        )
    elif len(password) < 4:
        logger.warning("⚠️ Пароль маленький")
        return JSONResponse(
            {
                "error": "empty_password",
                "message": "Пароль должен быть от 4 символов"
            },
            status_code=400
        )

    # ===== Управление сессиями =====
    session_id = request.cookies.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())
        logger.info(f"🆕 Новая сессия создана: {session_id}")

    # Проверка/установка пароля сессии
    session = await session_manager.get_or_create_session(session_id)
    is_first_auth = session.get("password", {}).get("hash") is None

    if is_first_auth:
        # ✅ НОВОЕ: Первая авторизация
        await session_manager.set_password(session_id, password)
        logger.info(f"🔐 Пароль установлен для сессии {session_id}")
        logger.info(f"set_password, password = {password} session_id = {session_id}")

        try:
            welcome_message = gigachat_client.chat()

            logger.info(f"welcome_message = {welcome_message}")
            logger.info(f"✅ Приветственное сообщение сгенерировано")

            await session_manager.add_to_history(
                session_id,
                agent_key=gigachat_client.get_current_agent().id,
                role="agent",
                content=welcome_message,
                timestamp=get_time_now()
            )

            history = await session_manager.get_history(session_id)

            response = JSONResponse(QuestionResponse(history=history).model_dump())
            # AuthResponse
            response.set_cookie(
                "session_id",
                session_id,
                httponly=True,
                max_age=86400,
                secure=False,
                samesite="lax"
            )

            logger.info(f"✅ Первая авторизация завершена для сессии {session_id}")
            return response

        except Exception as er:
            logger.error(f"💥 Критическая ошибка: {er}", exc_info=True)
            return JSONResponse(
                ErrorResp(
                    error=f"Internal server error",
                    message=f"💥 Критическая ошибка: {er}"
                ).model_dump(),
                status_code=500
            )

    else:
        # ✅ Повторная авторизация - проверяем пароль
        is_valid = await session_manager.verify_password(session_id, password)
        if not is_valid:
            logger.warning(f"❌ Неверный пароль для сессии {session_id}")
            return JSONResponse(
                ErrorResp(
                    error=f"wrong password",
                    message=f"💥 Неверный пароль для сессии"
                ).model_dump(),
                status_code=401
            )

        logger.info(f"✅ Пароль проверен для сессии {session_id}")

    agent_key = await session_manager.get_agent_key(session_id)

    agent = get_catalog().get_agent_by_key(agent_key) if agent_key else None

    if agent:
        message = gigachat_client.set_agent(agent)
        if message:
            await session_manager.add_to_history(
                session_id,
                agent_key=gigachat_client.get_current_agent().id,
                role="agent",
                content=message.content,
                timestamp=get_time_now()
            )

    # ===== Получение истории из сессии =====
    history = await session_manager.get_history(session_id)
    logger.info(f"📜 История получена: {len(history)} сообщений")
    # ===== Формирование ответа =====
    response = JSONResponse(QuestionResponse(history=history).model_dump())
    response.set_cookie(
        "session_id",
        session_id,
        httponly=True,
        max_age=86400,
        secure=False,
        samesite="lax"
    )

    logger.info(f"✅ Запрос успешно обработан для сессии {session_id}")
    return response


@app.post("/api/question")
async def question(request: Request, question_user: Question):
    # ===== Управление сессиями =====
    session_id = request.cookies.get("session_id")
    if not session_id:
        logger.error("session_id = null")
        return JSONResponse(
            ErrorResp(
                error=f"Session Error",
                message=f"💥 Сессия закончена"
            ).model_dump(),
            status_code=400
        )
    password = question_user.password.strip()
    is_valid = await session_manager.verify_password(session_id, password)
    if not is_valid:
        logger.error(f"verify_password = false, password = {password} session_id = {session_id}")
        return JSONResponse(
            ErrorResp(
                error=f"Session Error",
                message=f"💥 Что-то с паролем"
            ).model_dump(),
            status_code=400
        )

    history = await session_manager.get_history(session_id)
    response_format = await session_manager.get_response_format(session_id)

    await session_manager.add_to_history(
        session_id,
        agent_key=gigachat_client.get_current_agent().id,
        role="user",  # ← роль пользователя
        content=question_user.question,
        timestamp=get_time_now()
    )

    message = gigachat_client.chat(
        question=question_user.question,
        history=history,
        additionally=response_format
    )
    logger.info(f"message = {message}")

    await session_manager.add_to_history(
        session_id,
        agent_key=gigachat_client.get_current_agent().id,
        role="agent",
        content=message,
        timestamp=get_time_now()
    )

    history = await session_manager.get_history(session_id)

    logger.info(f"history = {history}")

    response = JSONResponse(QuestionResponse(history=history).model_dump())
    # AuthResponse
    response.set_cookie(
        "session_id",
        session_id,
        httponly=True,
        max_age=86400,
        secure=False,
        samesite="lax"
    )

    logger.info(f"✅ Первая авторизация завершена для сессии {session_id}")
    return response


@app.get("/api/agents/list")
async def list_agents(request: Request):
    """
    Возвращает список всех доступных агентов.

    GET /api/agents/list

    Returns:
        JSON со списком агентов (Main, Manager, Custom)
    """
    agents = agent_catalog.list_available_agents()

    agents_data = [
        {
            "id": agent.id,
            "name": agent.name,
            "type": agent.agent_type.value,
            "temperature": agent.temperature,
            "model": agent.model
        }
        for agent in agents
    ]

    logger.info(f"📋 Список агентов: {len(agents_data)} агентов")
    return JSONResponse({
        "success": True,
        "count": len(agents_data),
        "agents": agents_data
    })


@app.get("/api/agents/{agent_key}")
async def get_agent_info(request: Request, agent_key: str):
    """
    Получает информацию об агенте по ID.

    GET /api/agents/{agent_id}

    Returns:
        JSON с полной конфигурацией агента
    """
    agent = agent_catalog.get_agent_by_key(agent_key)
    if not agent:
        return JSONResponse(
            {"error": "Agent not found"},
            status_code=404
        )

    logger.info(f"📋 Информация об агенте: {agent.name}")
    return JSONResponse({
        "success": True,
        "agent": agent
    })


@app.post("/api/model/set_temperature")
async def set_model_temperature(request: Request, config: ModelConfig):
    """
    Устанавливает конфигурацию модели.

    POST /api/model/set
    {
        "model": "GigaChat-2-Pro",
        "temperature": 0.7
    }
    """
    gigachat_client.set_temperature(config.temperature)

    logger.info(f"⚙️ Конфигурация модели обновлена")
    return JSONResponse({
        "success": True,
    })


@app.post("/api/model/set_response_format")
async def set_model_response_format(request: Request, config: ModelConfig):
    """
    Устанавливает конфигурацию модели.

    POST /api/model/set
    {
        "model": "GigaChat-2-Pro",
        "temperature": 0.7
    }
    """

    session_id = request.cookies.get("session_id")
    if not session_id:
        return JSONResponse(
            ErrorResp(
                error=f"Session Error",
                message=f"💥 Сессия закончена"
            ).model_dump(),
            status_code=400
        )

    await session_manager.set_response_format(session_id, config.response_format)

    logger.info(f"⚙️ Конфигурация модели обновлена")
    return JSONResponse({
        "success": True,
    })


@app.post("/api/model/set_new_agent")
async def set_model_response_format(request: Request, config: ModelConfig):
    """
    Устанавливает модели.
    """
    session_id = request.cookies.get("session_id")
    if not session_id:
        return JSONResponse(
            ErrorResp(
                error=f"Session Error",
                message=f"💥 Сессия закончена"
            ).model_dump(),
            status_code=400
        )
    agent = agent_catalog.get_agent_by_key(config.agent_key)
    if agent:
        message = gigachat_client.set_agent(agent)
        if message:
            await session_manager.add_to_history(
                session_id,
                agent_key=gigachat_client.get_current_agent().id,
                role="agent",
                content=message.content,
                timestamp=get_time_now()
            )

        logger.info(f"⚙️ Конфигурация модели обновлена")
        return JSONResponse({
            "success": True,
        })
    else:
        logger.error(f"⚙️ Конфигурация модели не обновлена")
        return JSONResponse({
            "success": False,
        })


# ===== Обработка ошибок =====
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Глобальный обработчик исключений."""
    logger.error(f"💥 Необработанное исключение: {exc}", exc_info=True)
    logger.error(f"💥 request.state: {request.state}")
    return JSONResponse(
        ErrorResp(
            error=f"Internal server error",
            message=f"💥 {str(exc)}"
        ).model_dump(),
        status_code=500
    )


# ===== Вспомогательные функции =====

def print_startup_info():
    """Выводит информацию о запуске приложения."""
    print("\n" + "=" * 70)
    print("🚀 GigaChat Agent - Веб-сервер запущен")
    print("=" * 70)
    print("\n📍 Адреса доступа:")
    print("   - Веб-интерфейс: http://127.0.0.1:8010/chat")
    print("   - API документация: http://127.0.0.1:8010/docs")
    print("   - Альтернативная документация: http://127.0.0.1:8010/redoc")
    print("\n🤖 Компоненты:")
    print(f"   - GigaChat клиент: ✅")
    print(f"   - Система агентов: ✅")
    print(f"   - Управление сессиями: ✅")
    print(f"   - Инструменты (Tools): ✅")
    print("\n" + "=" * 70 + "\n")
