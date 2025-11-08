"""
Константы и конфигурация для проекта GigaChat Agent.
"""
from __future__ import annotations

from typing import Final


KEY_SELECTED_AGENT_SYSTEMS: Final[str] = "selected_agent_systems"
KEY_SELECTED_FORMAT_TYPE_REQUEST: Final[str] = "selected_format_type_request"
KEY_SELECTED_FORMAT_REQUEST: Final[str] = "selected_format_request"
KEY_PASSWORD_SALT: Final[str] = "password_salt"
KEY_SESSION_ID: Final[str] = "session_id"

# ИНСТРУМЕНТЫ
MAX_FILE_SIZE: Final[int] = 10 * 1024 * 1024  # 10MB
MAX_FILE_READ_SIZE: Final[int] = 1 * 1024 * 1024  # 1MB
ONE_DAY_IN_SECONDS: Final[int] = 60 * 60 * 24 # 1 день # секунды
