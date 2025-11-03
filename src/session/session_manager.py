"""
Асинхронный менеджер сессий.

Отслеживает истории диалогов, пароли и системные промпты для каждой сессии.
"""

import json
import hashlib
import os
import secrets
import logging
import tempfile
from typing import Any, Dict, List, Optional
from pathlib import Path
from datetime import datetime, timezone
import asyncio
from functools import partial

logger = logging.getLogger(__name__)

# Директория для сохранения сессий
SESSIONS_DIR = Path("data/sessions")
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


def _blocking_read_json(path: Path) -> Dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
        return json.loads(text)
    except Exception as e:
        # Возвращаем пустой объект при ошибке чтения/парсинга
        logger.exception("blocking read json error for %s: %s", path, e)
        return {}


def _blocking_write_json_atomic(path: Path, data: Dict[str, Any]) -> None:
    """
    Блокирующая атомарная запись JSON: пишем во временный файл, затем os.replace.
    Выполняется в executor-е.
    """
    text = json.dumps(data, indent=2, ensure_ascii=False)
    dirpath = str(path.parent)
    fd, tmp_path = tempfile.mkstemp(prefix=path.name, dir=dirpath, text=True)
    try:
        # fdopen использует файловый дескриптор, гарантируем sync на диск
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
            f.flush()
            try:
                os.fsync(f.fileno())
            except Exception:
                # fsync может отсутствовать на некоторых FS — не критично
                pass
        os.replace(tmp_path, str(path))
    except Exception:
        logger.exception("blocking write json error for %s", path)
        # попытаться удалить tmp
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass


def _blocking_remove_file(path: Path) -> None:
    try:
        if path.exists():
            path.unlink()
    except Exception:
        logger.exception("blocking remove file error for %s", path)


class SessionManager:
    """Менеджер сессий с поддержкой паролей и систем.промптов."""

    def __init__(self, sessions_dir: Optional[Path] = None) -> None:
        """
        Инициализирует менеджер.

        Args:
            sessions_dir: Директория для сессий
        """
        self.sessions_dir = sessions_dir or SESSIONS_DIR
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        # Lock для модификаций одной сессии
        self._lock = asyncio.Lock()

    @staticmethod
    def _default_session(session_id: str) -> Dict[str, Any]:
        return {
            "session_id": session_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "password": {"hash": None, "salt": None},
            "system_prompt": {"prompt": "", "tag": None},
            "history": []
        }

    # ----------------------- ЧТЕНИЕ / ЗАПИСЬ ЧЕРЕЗ EXECUTOR -----------------------

    @staticmethod
    async def _read_json(path: Path) -> Dict[str, Any]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(_blocking_read_json, path))

    @staticmethod
    async def _write_json_atomic(path: Path, data: Dict[str, Any]) -> None:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(_blocking_write_json_atomic, path, data))

    @staticmethod
    async def _remove_file(path: Path) -> None:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(_blocking_remove_file, path))

    # --------------------------- ОСНОВНАЯ ЛОГИКА ---------------------------

    async def get_or_create_session(self, session_id: str) -> Dict[str, Any]:
        """
        Получает или создаёт сессию.
        """
        session_file = self.sessions_dir / f"{session_id}.json"

        if session_file.exists():
            session = await self._read_json(session_file)
            # Если чтение упало и вернулась пустая dict, вернём default
            if session:
                return session

        # создаём новую сессию и атомарно записываем (без lock)
        session = self._default_session(session_id)
        await self._write_json_atomic(session_file, session)
        logger.info("Session created: %s", session_id)
        return session

    async def verify_password(self, session_id: str, password: str) -> bool:
        """
        Проверяет пароль сессии.
        """
        session = await self.get_or_create_session(session_id)

        if session["password"]["hash"] is None:
            # Первый раз - установляем пароль
            await self.set_password(session_id, password)
            return True

        # Проверяем пароль
        salt = session["password"]["salt"]
        expected_hash = self._hash_password(password, salt)

        return expected_hash == session["password"]["hash"]

    async def set_password(self, session_id: str, password: str) -> None:
        """
        Устанавливает пароль — захватываем lock только здесь.
        Важно: не вызывать другие методы, которые берут lock.
        """
        async with self._lock:
            # читаем без lock, т.к. get_or_create_session не берёт lock
            session = await self.get_or_create_session(session_id)

            salt = secrets.token_hex(16)
            password_hash = self._hash_password(password, salt)

            session["password"]["hash"] = password_hash
            session["password"]["salt"] = salt

            session_file = self.sessions_dir / f"{session_id}.json"
            await self._write_json_atomic(session_file, session)
            logger.info("Password set for session: %s", session_id)

    async def set_system_prompt(self, session_id: str, prompt: str) -> bool:
        """
        Устанавливает системный промпт.

        Args:
            session_id: ID сессии
            prompt: Текст промпта

        Returns:
            bool: Успешно ли установлен
        """
        async with self._lock:
            session = await self.get_or_create_session(session_id)

            session["system_prompt"]["prompt"] = prompt
            session["system_prompt"]["tag"] = "system_prompt"

            session_file = self.sessions_dir / f"{session_id}.json"
            await self._write_json_atomic(session_file, session)
            logger.info("System prompt set for session: %s", session_id)
            return True

    async def get_system_prompt(self, session_id: str) -> Optional[Dict]:
        """
        Получает системный промпт.

        Args:
            session_id: ID сессии

        Returns:
            Dict или None: Системный промпт
        """
        session = await self.get_or_create_session(session_id)
        prompt_data = session.get("system_prompt", {})

        if prompt_data.get("prompt"):
            return {"prompt": prompt_data["prompt"], "tag": prompt_data.get("tag")}
        return None

    async def get_response_format(self, session_id: str) -> Optional[Dict[str, str]]:
        """
        Получает response_format.
        """
        session = await self.get_or_create_session(session_id)
        return session.get("response_format")

    async def set_response_format(self, session_id: str, response_format: Optional[Dict[str, str]]):
        """
        Сохраняет response_format.
        """
        async with self._lock:
            # читаем без lock, т.к. get_or_create_session не берёт lock
            session = await self.get_or_create_session(session_id)
            session["response_format"] = response_format

            session_file = self.sessions_dir / f"{session_id}.json"
            await self._write_json_atomic(session_file, session)
            logger.info("response_format set for session: %s", session_id)

    async def add_to_history(
            self,
            session_id: str,
            agent_key: str,
            role: str,
            content: str,
            timestamp: Optional[str] = None
    ) -> bool:
        """
        Добавляет сообщение в историю.
        """
        async with self._lock:
            session = await self.get_or_create_session(session_id)

            if timestamp is None:
                timestamp = datetime.now(timezone.utc).strftime("%H:%M")

            session["history"].append({
                "role": role,
                "content": content,
                "agent_key": agent_key,
                "time": timestamp,
                "prompt_tag": ""
            })

            # Ограничиваем историю 100 сообщениями
            if len(session["history"]) > 100:
                session["history"] = session["history"][-100:]

            session_file = self.sessions_dir / f"{session_id}.json"
            await self._write_json_atomic(session_file, session)
            return True

    async def add_to_history_with_prompt(
            self,
            session_id: str,
            role: str,
            agent_key: str,
            set_response_format: Dict[str, str],
            content: str,
            timestamp: str,
            prompt_tag: Optional[str] = None
    ) -> bool:
        # should_add_to_history теперь async — читаем без lock
        if not await self.should_add_to_history(session_id, prompt_tag):
            logger.debug("Duplicate message skipped for session %s", session_id)
            return False

        async with self._lock:
            session = await self.get_or_create_session(session_id)

            session["history"].append({
                "role": role,
                "content": content,
                "agent_key": agent_key,
                "set_response_format": set_response_format,
                "time": timestamp,
                "prompt_tag": prompt_tag
            })

            if len(session["history"]) > 100:
                session["history"] = session["history"][-100:]

            session_file = self.sessions_dir / f"{session_id}.json"
            await self._write_json_atomic(session_file, session)
            return True

    async def should_add_to_history(self, session_id: str, prompt_tag: Optional[str]) -> bool:
        """
        Асинхронная проверка для добавления в историю — НЕ берём lock.
        """
        session_file = self.sessions_dir / f"{session_id}.json"

        if not session_file.exists():
            return True

        session = await self._read_json(session_file)
        history = session.get("history", [])

        if not history:
            return True

        last_msg = history[-1]
        if last_msg.get("prompt_tag") == prompt_tag and prompt_tag is not None:
            return False

        return True

    async def get_history(self, session_id: str) -> List[Dict]:
        """
        Получает историю сессии.

        Args:
            session_id: ID сессии

        Returns:
            List[Dict]: История сообщений
        """
        session = await self.get_or_create_session(session_id)
        return session.get("history", [])

    async def get_agent_key(self, session_id: str) -> Optional[str]:
        """
        Получает ключ агента.
        """
        session = await self.get_or_create_session(session_id)
        return session.get("agent_key")

    async def clear_history(self, session_id: str) -> bool:
        """Очищает историю сессии."""
        async with self._lock:
            session = await self.get_or_create_session(session_id)
            session["history"] = []

            session_file = self.sessions_dir / f"{session_id}.json"
            await self._write_json_atomic(session_file, session)
            return True

    async def delete_session(self, session_id: str) -> bool:
        """Удаляет сессию."""
        async with self._lock:
            session_file = self.sessions_dir / f"{session_id}.json"

            if session_file.exists():
                await self._remove_file(session_file)
                logger.info("Session deleted: %s", session_id)
                return True

            return False

    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        """Хеширует пароль с солью."""
        return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()


# глобальный менеджер
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Получить менеджер сессий."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
