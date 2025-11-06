import logging
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from langchain_gigachat.chat_models import GigaChat
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from src.config.settings import AUTH_KEY, SCOPE, CERTIFICATE_PATH

from src.config.constants import (
    AgentType,
    GigaChatModel,
    DEFAULT_AGENT_TEMPERATURE,
    DEFAULT_AGENT_MAX_CONTEXT,
    DEFAULT_AGENT_MAX_TOKENS,
    DEFAULT_SYSTEM_PROMPT,
    DEFAULT_AGENT_NAME,
    HELLO_PROMPT,
    TAG_SYSTEM_PROMPT,
    TAG_USER_PROMPT,
    TAG_HELLO_PROMPT,
    TAG,
)

logger = logging.getLogger(__name__)


class AgentBase:
    """
    Базовый класс для всех агентов в системе.
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
            metadata: Optional[Dict[str, Any]] = None,
            credentials: str = AUTH_KEY,
            scope: str = SCOPE,
            ca_bundle_file: Optional[str] = CERTIFICATE_PATH,
    ) -> None:

        if not credentials:
            raise RuntimeError(
                "Не указан ключ авторизации GigaChat API. "
                "Установите переменную окружения GIGACHAT_TOKEN или передайте credentials."
            )

        self._credentials = credentials
        self._scope = scope
        self._ca_bundle_file = ca_bundle_file

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

        # Инициализация LangChain GigaChat модели
        self._llm = self._create_llm()
        logger.info(f"Agent created: {self.name} (ID: {self.id}, Type: {self.agent_type.value})")


    def _create_llm(self) -> GigaChat:
        return GigaChat(
            credentials=self._credentials,
            scope=self._scope,
            model=self.model.value,
            temperature=self.temperature,
            verify_ssl_certs=self._ca_bundle_file is not None,
            ca_bundle_file=self._ca_bundle_file  # Может быть None
        )

    def create_llm(self) -> Optional[BaseMessage]:
        self._llm = self._create_llm()
        if self.hello_prompt:
            return self.build_messages()
        else:
            return None

    def build_messages(
            self,
            question: str = "",
            history: List[Dict[str, str]] = None,
            additionally: Dict[str, str] = None
    ) -> BaseMessage:
        """Формирует сообщения для модели (можно переопределять в наследниках)."""

        if not history:
            history = []
        messages: List[Any] = [
            SystemMessage(
                content=self.system_prompt,
                kwargs={TAG, TAG_SYSTEM_PROMPT}
            )
        ]

        if self.hello_prompt and not history:
            messages.append(self.hello_prompt)
            return self._llm.invoke(messages)

        user_prompt: HumanMessage | None = None

        recent_messages: List[Any] = []
        num_messages = min(len(history), self.max_context_messages)
        for msg in history[-num_messages:]:
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
        return self._llm.invoke(messages)

    def __repr__(self) -> str:
        return f"<Agent {self.name} (ID: {self.id}, Type: {self.agent_type.value})>"
