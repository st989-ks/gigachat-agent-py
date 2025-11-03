"""
Модуль агентов - управление агентами и их выполнение.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from src.config.constants import TagFormatResponse
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from src.config.constants import (
    AgentType,
    GigaChatModel,
    DEFAULT_AGENT_TEMPERATURE,
    DEFAULT_AGENT_MODEL,
    DEFAULT_AGENT_MAX_CONTEXT,
    DEFAULT_AGENT_MAX_TOKENS,
    DEFAULT_SYSTEM_PROMPT,
    DEFAULT_AGENT_NAME,
    DEFAULT_AGENT_TYPE,
    HELLO_PROMPT,
    TAG_SYSTEM_PROMPT,
    TAG_USER_PROMPT,
    TAG_HELLO_PROMPT,
    TAG_FORMAT,
    TAG,
)

logger = logging.getLogger(__name__)


class Agent:
    """
    Базовый класс для всех агентов в системе.

    Attributes:
        :param id: Уникальный идентификатор агента
        :param name: Имя агента
        :param agent_type: Тип агента (MAIN, BASIC, CUSTOM)
        :param temperature: Температура генерации (0.0-2.0)
        :param model: Используемая модель GigaChat
        :param system_prompt: Системная инструкция для агента
        :param tools_ids: Список ID инструментов, которые может использовать агент
        :param max_context_messages: Максимум сообщений в контексте
        :param max_tokens: Максимальное количество токенов в ответе
        :param metadata: Дополнительные метаданные
    """

    def __init__(
            self,
            id_agent: str = str(uuid.uuid4())[:8],
            name: str = DEFAULT_AGENT_NAME,
            agent_type: AgentType = AgentType.MAIN,
            temperature: float = DEFAULT_AGENT_TEMPERATURE,
            model: GigaChatModel = GigaChatModel.GIGACHAT_2,
            system_prompt: str = DEFAULT_SYSTEM_PROMPT,
            hello_prompt: Optional[HumanMessage] = HELLO_PROMPT,
            tools_ids: List[int] = None,
            max_context_messages: int = DEFAULT_AGENT_MAX_CONTEXT,
            max_tokens: int = DEFAULT_AGENT_MAX_TOKENS,
            metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        self.id = id_agent
        self.name = name
        self.agent_type = agent_type
        self.temperature = temperature
        self.model = model
        self.system_prompt = system_prompt
        self.hello_prompt = hello_prompt
        self.tools_ids = tools_ids
        self.max_context_messages = max_context_messages
        self.max_tokens = max_tokens
        self.metadata = metadata or {}
        self.created_at = datetime.now(timezone.utc).isoformat()

        logger.info(f"Agent created: {self.name} (ID: {self.id}, Type: {self.agent_type.value})")

    def build_messages(
            self,
            question: str = "",
            history: List[Dict[str, str]] = None,
            additionally: Dict[str, str] = None
    ) -> List[Any]:
        """Формирует сообщения для модели (можно переопределять в наследниках)."""
        messages: List[Any] = [
            SystemMessage(
                content=self.system_prompt,
                kwargs={TAG, TAG_SYSTEM_PROMPT}
            )
        ]

        if self.hello_prompt and not history:
            messages.append(self.hello_prompt)
            return messages

        user_prompt: HumanMessage | None = None

        recent_messages: List[Any] = []
        for msg in history[-self.max_context_messages:]:
            role = msg.get("role", "")
            content = msg.get("content", "")
            tag = msg.get("tag", "")

            if tag in (TAG_SYSTEM_PROMPT, TAG_HELLO_PROMPT):
                continue

            if tag == TAG_USER_PROMPT:
                user_prompt = HumanMessage(
                    content=content,
                    kwargs={TAG, TAG_USER_PROMPT}
                )
            elif role == "user":
                recent_messages.append(HumanMessage(content=content))
            elif role == "agent":
                recent_messages.append(AIMessage(content=content))

        if user_prompt:
            messages.append(user_prompt)

        messages.extend(recent_messages)

        messages.append(HumanMessage(content=question))
        return messages

    def __repr__(self) -> str:
        return f"<Agent {self.name} (ID: {self.id}, Type: {self.agent_type.value})>"


class FormatterAgent(Agent):

    def __init__(self):
        super().__init__(
            id_agent="formater",
            name="Agent Formatter",
            agent_type=AgentType.BASIC,
            temperature=0.1,
            model=GigaChatModel.GIGACHAT_2_MAX,
            system_prompt=(
                "Ты — системный агент, отвечающий СТРОГО в заданном формате.\n\n"
                "ПРАВИЛА:\n"
                "1. Если задан формат [JSON], выводи ТОЛЬКО валидный JSON без текста вне структуры.\n"
                "2. Если задан формат [XML], выводи ТОЛЬКО XML с корректной иерархией.\n"
                "3. Без пояснений, без комментариев, без вводных слов.\n"
                "4. Не добавляй Markdown-подсветку или кавычки.\n"
                "5. Ответ — это ТОЛЬКО тело структуры данных.\n\n"
                "ВАЖНО: Если поля не совпадают с примером, используй точно такие же имена!\n"
            ),
            hello_prompt=None,
            tools_ids=[],
            max_context_messages=15,
            max_tokens=20000,
            metadata={"predefined": True, "role": "formatter", "version": "1.0"}
        )

    def build_messages(
            self,
            question: str = "",
            history: List[Dict[str, str]] = None,
            additionally: Dict[str, str] = None
    ) -> List[Any]:
        """Формирует минимальный контекст — только системное сообщение и текущий вопрос."""

        if additionally is None:
            additionally = {}
        format_tag = additionally.get(TAG, TagFormatResponse.DEFAULT.value)
        format_structure = additionally.get(TAG_FORMAT, "")

        system_format_message = SystemMessage(
            content=f"{self.system_prompt}\n\n Формат ответа {format_tag}: \n\n {format_structure}",
            kwargs={TAG, TAG_SYSTEM_PROMPT}
        )
        logger.info(system_format_message)
        messages: List[Any] = [
            system_format_message,
            HumanMessage(content=question)
        ]
        return messages


class MainAgent(Agent):

    def __init__(self):
        super().__init__(
            id_agent="main",
            name="Главный агент",
            agent_type=AgentType.MAIN,
            temperature=0.7,
            model=GigaChatModel.GIGACHAT_2,
            system_prompt=(
                "Ты Вассерман Анатолий. Роль: "
                "1) Анализировать запросы пользователей. "
                "2) При необходимости составлять предварительные планы работы. "
                "3) Собирать дополнительную информацию если ее недостаточно. "
                "4) Будь дружелюбным, точным, информативным, и лаконичный, допускается дружественная дерзость"
            ),
            hello_prompt=HELLO_PROMPT,
            tools_ids=[],
            max_context_messages=20,
            max_tokens=10000,
            metadata={"predefined": True, "version": "1.0"}
        )


class AgentCatalog:
    """
        Каталог и фабрика агентов.
    """

    _agents: Dict[str, Agent] = {}

    def __init__(self) -> None:
        """Инициализирует каталог."""
        self._agents = {}
        self._register_predefined_agents()

    def _register_predefined_agents(self) -> None:
        """Регистрирует предопределенные агенты."""
        self._agents = {
            "main": MainAgent(),
            "formater": FormatterAgent(),
        }
        for agent in self._agents.values():
            logger.info(f"Agent created: {agent.name} (ID: {agent.id})")

    def create_agent(self, spec: Dict[str, Any]) -> Agent:
        agent = Agent(
            name=spec.get("name", DEFAULT_AGENT_NAME),
            agent_type=spec.get("agent_type", DEFAULT_AGENT_TYPE),
            temperature=spec.get("temperature", DEFAULT_AGENT_TEMPERATURE),
            model=spec.get("model", DEFAULT_AGENT_MODEL),
            system_prompt=spec.get("system_prompt", DEFAULT_SYSTEM_PROMPT),
            hello_prompt=spec.get("hello_prompt", HELLO_PROMPT),
            tools_ids=spec.get("tools_ids"),
            max_context_messages=spec.get("max_context_messages", DEFAULT_AGENT_MAX_CONTEXT),
            max_tokens=spec.get("max_tokens", DEFAULT_AGENT_MAX_TOKENS),
            metadata=spec.get("metadata", {})
        )

        self._agents[agent.id] = agent
        logger.info(f"Agent created: {agent.name} (ID: {agent.id})")

        return agent

    def get_agent_by_key(self, agent_key: str) -> Optional[Agent]:
        """Получает агента по Ключу."""
        return self._agents.get(agent_key)

    def list_available_agents(self) -> List[Agent]:
        """Возвращает список всех доступных агентов."""
        return list(self._agents.values())


_catalog = None


def get_catalog() -> AgentCatalog:
    """Получить глобальный каталог агентов."""
    global _catalog
    if _catalog is None:
        _catalog = AgentCatalog()
    return _catalog
