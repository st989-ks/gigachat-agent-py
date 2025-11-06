"""
Константы и конфигурация для проекта GigaChat Agent.
"""
from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Final, Dict
from langchain_core.messages import SystemMessage, HumanMessage

# ПУТИ И ДИРЕКТОРИИ
PROJECT_ROOT: Final[Path] = Path(__file__).parent.parent
LOGS_DIR: Final[Path] = PROJECT_ROOT / "logs"
DATA_DIR: Final[Path] = PROJECT_ROOT / "data"

# Создаём директории при импорте если их нет
for directory in [LOGS_DIR, DATA_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

class TagFormatResponse(str, Enum):
    JSON = "[JSON]"
    XML = "[XML]"
    DEFAULT = "[DEFAULT]"


class GigaChatModel(str, Enum):
    """Доступные модели GigaChat."""
    GIGACHAT_2 = "GigaChat-2"
    GIGACHAT_2_PRO = "GigaChat-2-Pro"
    GIGACHAT_2_MAX = "GigaChat-2-Max"

    @classmethod
    def from_any(cls, value: str | GigaChatModel) -> GigaChatModel:
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            if value in cls.__members__:
                return cls[value]  # type: ignore
            for m in cls:
                if m.value == value:
                    return m
        raise ValueError(f"Unknown GigaChatModel: {value}")


class AgentType(str, Enum):
    """Типы агентов в системе."""
    MAIN = "main"
    BASIC = "basic"
    CUSTOM = "custom"

    @classmethod
    def from_any(cls, value: str | AgentType) -> AgentType:
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            if value in cls.__members__:
                return cls[value]  # type: ignore
            for m in cls:
                if m.value == value:
                    return m
        raise ValueError(f"Unknown AgentType: {value}")


class ToolCategory(str, Enum):
    """Категории инструментов."""
    FILE_OPERATIONS = "file_operations"
    WEB_OPERATIONS = "web_operations"
    DATA_PROCESSING = "data_processing"
    VERSION_CONTROL = "version_control"
    AGENT_OPERATIONS = "agent_operations"
    REGEX_OPERATIONS = "regex_operations"
    CALCULATIONS = "calculations"


# ЛОГИРОВАНИЕ
AGENTS_LOG_FILE: Final[Path] = LOGS_DIR / "agents.log"
SESSION_LOG_FILE: Final[Path] = LOGS_DIR / "session_manager.log"
CUSTOM_AGENTS_LOG: Final[Path] = DATA_DIR / "custom_agents_log.json"

LOG_FORMAT: Final[str] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL: Final[str] = "INFO"
LOG_MAX_BYTES: Final[int] = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT: Final[int] = 5

DEFAULT_REQUEST_TIMEOUT = 20

# АГЕНТЫ
DEFAULT_AGENT_TEMPERATURE: Final[float] = 0.87
DEFAULT_AGENT_MODEL: Final[GigaChatModel] = GigaChatModel.GIGACHAT_2
DEFAULT_AGENT_TYPE: Final[AgentType] = AgentType.BASIC
DEFAULT_AGENT_NAME: Final[str] = "Секретный агент"
DEFAULT_AGENT_MAX_CONTEXT: Final[int] = 10
DEFAULT_AGENT_MAX_TOKENS: Final[int] = 2048
DEFAULT_AGENT_TOOLS: Final[list] = []

TAG: Final[str] = "tag"
TAG_FORMAT: Final[str] = "format"
TAG_SYSTEM_PROMPT: Final[str] = "[SYSTEM_PROMPT]"
TAG_USER_PROMPT: Final[str] = "[USER_PROMPT]"
TAG_HELLO_PROMPT: Final[str] = "[HELLO_PROMPT]"

MIN_TEMPERATURE: Final[float] = 0.0
MAX_TEMPERATURE: Final[float] = 2.0
DEFAULT_SYSTEM_PROMPT: Final[str] = (
    "Ты дефолтный агент."
    "Твоя задача выслушать пользователя."
    "Ты в меру вежлив, но не проч и дерзить, но с умом."
    "Можешь помочь сориентировать пользователя по проекту."
)

PROMPT_MAP: Dict[str, str] = {
    "[JSON]": (
        "4.  Пишешь только формат [JSON], выводи ТОЛЬКО валидный JSON без текста вне структуры.\n"
        "ВАЖНО: Если поля не совпадают с примером, используй точно такие же имена!\n"
    ),
    "[XML]": (
        "4. Пишешь только формат [XML], выводи ТОЛЬКО XML с корректной иерархией.\n"
        "ВАЖНО: Если поля не совпадают с примером, используй точно такие же имена!\n"
    ),
}

DEFAULT_SYSTEM_MESSAGE: Final[SystemMessage] = SystemMessage(
    content=("Ты дефолтный агент."
             "Твоя задача выслушать пользователя."
             "Ты в меру вежлив, но не проч и дерзить, но с умом."
             "Можешь помочь сориентировать пользователя по проекту."),
    kwargs={TAG: TAG_SYSTEM_PROMPT}
)

HELLO_PROMPT: Final[HumanMessage] = HumanMessage(
    content="Поприветствую пользователя, и скажи что-нибудь приятное",
    kwargs={TAG: TAG_HELLO_PROMPT}
)

# Штраф за повторение слов (repetition_penalty)
# 1.0 - слова могут повторяться, >1.0 - повторения уменьшаются
REPETITION_PENALTY = 1.0

# ИНСТРУМЕНТЫ
MAX_FILE_SIZE: Final[int] = 10 * 1024 * 1024  # 10MB
MAX_FILE_READ_SIZE: Final[int] = 1 * 1024 * 1024  # 1MB
TOOL_TIMEOUT: Final[int] = 30  # секунды
