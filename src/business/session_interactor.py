import json
import hashlib
import os
import secrets
import logging
import tempfile
from typing import Any, Dict, Optional
from pathlib import Path
from datetime import datetime, timezone
import asyncio
from functools import partial

from src.core.configs import settings

logger = logging.getLogger(__name__)

def _blocking_read_json(path: Path) -> Dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
        return json.loads(text)  # type: Dict[str, Any]
    except Exception as e:
        logger.exception("blocking read json error for %s: %s", path, e)
        return {}


def _blocking_write_json_atomic(path: Path, data: Dict[str, Any]) -> None:
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

    def __init__(self, sessions_dir: Optional[Path] = None) -> None:
        self.sessions_dir = sessions_dir or settings.SESSIONS_DIR
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        # Lock для модификаций одной сессии
        self._lock = asyncio.Lock()

    @staticmethod
    def _default_session(session_id: str) -> Dict[str, Any]:
        return {
            "session_id": session_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "password": {"hash": None, "salt": None},
        }

    @staticmethod
    async def _read_json(path: Path) -> Dict[str, Any]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            executor=None,
            func=partial(_blocking_read_json, path)
        )

    @staticmethod
    async def _write_json_atomic(path: Path, data: Dict[str, Any]) -> None:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            executor=None,
            func=partial(_blocking_write_json_atomic, path, data)
        )

    @staticmethod
    async def _remove_file(path: Path) -> None:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            executor=None,
            func=partial(_blocking_remove_file, path)
        )

    async def get_or_create_session(self, session_id: str) -> Dict[str, Any]:
        session_file = self.sessions_dir / f"{session_id}.json"

        if session_file.exists():
            session = await self._read_json(session_file)
            logger.info(f"Создана новая сессия сессии {session_id}")
            if session:
                return session

        session = self._default_session(session_id)
        await self._write_json_atomic(session_file, session)
        logger.info("Session created: %s", session_id)
        return session

    async def verify_session(self, session_id: str, cookie_password_salt: str) -> Optional[str]:
        session = await self.get_or_create_session(session_id)
        password_salt: Optional[str] = session["password"]["salt"]
        return password_salt if password_salt == cookie_password_salt else None

    async def login(self, session_id: str, password: str) -> Optional[str]:
        session = await self.get_or_create_session(session_id)

        password_hash: Optional[str] = session["password"]["hash"]


        if not password_hash:
            password_hash = await self.set_password(session_id, password)

        salt: Optional[str] =  session["password"]["salt"]
        password_hash_check = self._hash_password(password, salt)

        return salt if password_hash == password_hash_check else None

    async def set_password(self, session_id: str, password: str) -> str:
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
            return salt

    async def delete_session(self, session_id: str) -> bool:
        async with self._lock:
            session_file = self.sessions_dir / f"{session_id}.json"

            if session_file.exists():
                await self._remove_file(session_file)
                logger.info("Session deleted: %s", session_id)
                return True

            return False

    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()


_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
