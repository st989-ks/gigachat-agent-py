"""
Константы и конфигурация для проекта GigaChat Agent.
"""
from __future__ import annotations

from typing import Final
from src.model.chat import Chat
from datetime import datetime


KEY_SELECTED_AGENT_SYSTEMS: Final[str] = "KEY_SELECTED_AGENT_SYSTEMS"
KEY_SELECTED_CHAT: Final[str] = "KEY_SELECTED_CHAT"
KEY_SELECTED_FORMAT_TYPE_REQUEST: Final[str] = "KEY_SELECTED_FORMAT_TYPE_REQUEST"
KEY_SELECTED_FORMAT_REQUEST: Final[str] = "KEY_SELECTED_FORMAT_REQUEST"
KEY_PASSWORD_SALT: Final[str] = "KEY_PASSWORD_SALT"
KEY_SESSION_ID: Final[str] = "KEY_SESSION_ID"

# ИНСТРУМЕНТЫ
MAX_FILE_SIZE: Final[int] = 10 * 1024 * 1024  # 10MB
MAX_FILE_READ_SIZE: Final[int] = 1 * 1024 * 1024  # 1MB
ONE_DAY_IN_SECONDS: Final[int] = 60 * 60 * 24 # 1 день # секунды


CHATS_DEFAULT: Final[list[Chat]] =[
    Chat(
        id="1",
        name="STANDART",
        created_at=None
    ),
    Chat(
        id="2",
        name="DAY_9",
        created_at=None
    ),
] 