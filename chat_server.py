#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os, requests
import uuid
import hashlib
import secrets
from datetime import datetime
from typing import Optional, List

app = FastAPI(title="GigaChat Agent")
app.mount("/static", StaticFiles(directory="static"), name="static")

class Query(BaseModel):
    question: str
    password: str = ""
    history: Optional[List[dict]] = []

# Конфигурация
AUTH_KEY = os.getenv("GIGACHAT_TOKEN")
SCOPE = "GIGACHAT_API_PERS"
OAUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
API_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

if not AUTH_KEY:
    raise RuntimeError("❌ Переменная окружения GIGACHAT_TOKEN не установлена")

# ===== ХРАНЕНИЕ ПАРОЛЕЙ И ИСТОРИИ ПО СЕССИЯМ =====
session_storage = {}  # {session_id: {"password": {...}, "history": [...]}}


def get_or_create_session(session_id: str):
    """
    Получает или создаёт новую сессию.
    """
    if session_id not in session_storage:
        session_storage[session_id] = {
            "password": None,
            "history": []
        }
    return session_storage[session_id]


def set_session_password(session_id: str, password: str) -> bool:
    """
    Устанавливает пароль для сессии при первом запросе.
    Возвращает True если пароль установлен, False если уже установлен.
    """
    session = get_or_create_session(session_id)

    if session["password"] is None:
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        session["password"] = {"hash": pwd_hash, "salt": salt}
        return True
    return False


def verify_session_password(session_id: str, password: str) -> bool:
    """
    Проверяет пароль против сохранённого хеша сессии.
    """
    session = get_or_create_session(session_id)

    if session["password"] is None:
        return False

    stored = session["password"]
    provided_hash = hashlib.sha256((password + stored["salt"]).encode()).hexdigest()
    return provided_hash == stored["hash"]


def add_to_history(session_id: str, role: str, content: str, timestamp: str):
    """
    Добавляет сообщение в историю сессии.
    """
    session = get_or_create_session(session_id)
    session["history"].append({
        "role": role,
        "content": content,
        "time": timestamp
    })


def get_session_history(session_id: str) -> list:
    """
    Возвращает историю сессии.
    """
    session = get_or_create_session(session_id)
    return session["history"]


def get_gigachat_token():
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "RqUID": str(uuid.uuid4()),
        "Authorization": f"Basic {AUTH_KEY}",
    }
    payload = {"scope": SCOPE}
    try:
        resp = requests.post(OAUTH_URL, headers=headers, data=payload, timeout=15, verify=False)
        resp.raise_for_status()
        data = resp.json()
        access_token = data.get("access_token")
        if not access_token:
            raise Exception("Не удалось получить токен доступа")
        return access_token
    except Exception as e:
        raise RuntimeError(f"Ошибка авторизации GigaChat: {e}")


@app.get("/chat", response_class=HTMLResponse)
async def chat_page():
    with open("static/index.html", encoding="utf-8") as f:
        return HTMLResponse(f.read())


@app.post("/api/verify-and-ask")
async def verify_and_ask(request: Request, query: Query):
    """
    Проверяет пароль и затем обращается к GigaChat API.
    При первом запросе сессии пароль устанавливается.
    История сообщений хранится на сервере для каждой сессии.
    """
    q = query.question.strip()
    pwd = query.password.strip()

    if not q:
        return JSONResponse({"error": "empty query"}, status_code=400)

    # Получаем session_id из cookies
    session_id = request.cookies.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())

    # Первый запрос - устанавливаем пароль
    if get_or_create_session(session_id)["password"] is None:
        if pwd.strip():
            set_session_password(session_id, pwd)
        else:
            return JSONResponse({"error": "empty_password"}, status_code=400)
    else:
        # Проверяем пароль для уже существующей сессии
        if not verify_session_password(session_id, pwd):
            return JSONResponse({"error": "wrong_password"}, status_code=401)

    try:
        # Получение токена авторизации
        token = get_gigachat_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # Получаем историю с сервера (последние 5 сообщений)
        server_history = get_session_history(session_id)
        messages = []

        for msg in server_history[-5:]:
            if msg.get("role") == "user":
                messages.append({"role": "user", "content": msg.get("content", "")})
            elif msg.get("role") == "agent":
                messages.append({"role": "assistant", "content": msg.get("content", "")})

        # Добавляем текущий вопрос
        messages.append({"role": "user", "content": q})

        payload = {
            "model": "GigaChat-2",
            "messages": messages,
            "n": 1,
            "stream": False,
            "max_tokens": 512,
            "repetition_penalty": 1,
            "update_interval": 0
        }
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=20, verify=False)
        if resp.status_code != 200:
            return JSONResponse({"error": f"Bad response: {resp.status_code}"}, status_code=500)
        data = resp.json()
        answer = data["choices"][0]["message"]["content"].strip()

        # Сохраняем сообщения в историю сессии на сервере
        timestamp = datetime.now().strftime("%H:%M")
        add_to_history(session_id, "user", q, timestamp)
        add_to_history(session_id, "agent", answer, timestamp)

        response = JSONResponse({"answer": answer})
        response.set_cookie("session_id", session_id, httponly=True, max_age=86400)
        return response
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("chat_server:app", host="127.0.0.1", port=8010, reload=True)
