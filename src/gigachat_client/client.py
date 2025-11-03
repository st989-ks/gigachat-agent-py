from typing import List, Dict, Optional
from langchain_gigachat.chat_models import GigaChat
from src.config.settings import AUTH_KEY, SCOPE, CERTIFICATE_PATH
from src.gigachat_client.agents import Agent, get_catalog


class GigaChatClient:
    """
        Клиент для работы с GigaChat API через LangChain.
    """

    def __init__(
            self,
            credentials: str = AUTH_KEY,
            scope: str = SCOPE,
            ca_bundle_file: Optional[str] = CERTIFICATE_PATH,
            agent: Agent = get_catalog().get_agent_by_key(agent_key="main")
    ):
        if not credentials:
            raise RuntimeError(
                "Не указан ключ авторизации GigaChat API. "
                "Установите переменную окружения GIGACHAT_TOKEN или передайте credentials."
            )

        self._credentials = credentials
        self._scope = scope
        self._ca_bundle_file = ca_bundle_file
        self._agent = agent

        # Инициализация LangChain GigaChat модели
        self._llm = self._create_llm()

    def _create_llm(self) -> GigaChat:
        """
        Создает экземпляр GigaChat модели с текущими настройками.
        """

        return GigaChat(
            credentials=self._credentials,
            scope=self._scope,
            model=self._agent.model.value,
            temperature=self._agent.temperature,
            verify_ssl_certs=self._ca_bundle_file is not None,
            ca_bundle_file=self._ca_bundle_file  # Может быть None
        )

    def set_temperature(self, temperature: float) -> None:
        self._agent.temperature = temperature
        self._llm = self._create_llm()

    def set_agent(self, agent: Agent) -> None:
        self._agent = agent
        self._llm = self._create_llm()  # Пересоздаем LLM с новой моделью

    def get_current_agent(self) -> Agent:
        return self._agent

    def chat(
            self,
            question: str = "",
            history: List[Dict[str, str]] = None,
            additionally: Dict[str, str] = None
    ) -> str:
        """
        Отправляет запрос в GigaChat API с учетом истории диалога.
        """
        messages = self._agent.build_messages(
            question=question,
            history=history,
            additionally=additionally
        )
        response = self._llm.invoke(messages)

        # Возвращаем текстовое содержимое ответа
        return response.content
