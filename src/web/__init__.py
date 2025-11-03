"""
Веб-сервер FastAPI для GigaChat Agent.

Этот модуль предоставляет REST API и веб-интерфейс для взаимодействия
с GigaChat моделями через LangChain.

Основные эндпоинты:
    GET /chat - HTML страница чата
    POST /api/verify-and-ask - Отправка сообщения в GigaChat

Архитектура:
    - FastAPI для обработки HTTP запросов
    - Статические файлы (HTML/CSS/JS) в папке static/
    - Управление сессиями через cookies
    - Интеграция с GigaChatClient для работы с API

Пример запуска:
    uvicorn web.server:app --host 127.0.0.1 --port 8010 --reload
"""
