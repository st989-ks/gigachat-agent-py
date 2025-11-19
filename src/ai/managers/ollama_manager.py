import logging
from typing import Dict, Optional, Tuple, Any
from langchain_ollama import ChatOllama
from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableConfig
from src.model.agent import Agent
from src.model.chat_models import OllamaModel

logger = logging.getLogger(__name__)


class OllamaModelManager:
    """
    Менеджер для работы с локальными Ollama моделями
    Поддерживает кеширование, async операции и streaming
    """

    DEFAULT_TEMPERATURE: float = 0.7
    DEFAULT_MAX_TOKENS: int = 8000
    DEFAULT_BASE_URL: str = "http://localhost:11434"

    def __init__(self, base_url: str = DEFAULT_BASE_URL):
        self.base_url = base_url
        self._models: Dict[Tuple[OllamaModel, Optional[float], Optional[int]], ChatOllama] = {}
        self._last_params: Dict[OllamaModel, Tuple[Optional[float], Optional[int]]] = {}
        logger.info(f"OllamaModelManager init with base_url={base_url}")

    def get_model(
            self,
            model_type: OllamaModel,
            temperature: Optional[float] = None,
            max_tokens: Optional[int] = None,
            mcp_tools: Optional[Dict[str, Any]] = None,  # Параметр для передачи инструментов MCP
    ) -> ChatOllama:
        """Получить или создать экземпляр модели с кешированием и настройками инструментов"""

        # Используем last params если параметры не указаны
        if model_type in self._last_params:
            last_temp, last_max_tokens = self._last_params[model_type]
        else:
            last_temp = self.DEFAULT_TEMPERATURE
            last_max_tokens = self.DEFAULT_MAX_TOKENS

        temperature = temperature if temperature is not None else last_temp
        max_tokens = max_tokens if max_tokens is not None else last_max_tokens

        cache_key = (model_type, temperature, max_tokens)

        if cache_key not in self._models:
            self._models[cache_key] = ChatOllama(
                model=model_type.value,
                base_url=self.base_url,
                temperature=temperature,
                num_predict=max_tokens,
            )
            logger.info(f"[OllamaManager] Создана новая модель: {model_type.value}")

        self._last_params[model_type] = (temperature, max_tokens)
        return self._models[cache_key]

    def invoke(
            self,
            agent: Agent,
            input_messages: LanguageModelInput,
            config: Optional[RunnableConfig] = None,
            *,
            stop: Optional[list[str]] = None,
            **kwargs: Any,
    ) -> BaseMessage:
        """Синхронный вызов модели"""
        logger.info(f"OllamaModelManager invoke [{agent.name}]")
        return self.get_model(
            model_type=OllamaModel(agent.model),
            temperature=agent.temperature,
            max_tokens=agent.max_tokens,
        ).invoke(
            input=input_messages,
            config=config,
            stop=stop,
            **kwargs
        )

    async def ainvoke(
            self,
            agent: Agent,
            input_messages: LanguageModelInput,
            config: Optional[RunnableConfig] = None,
            *,
            stop: Optional[list[str]] = None,
            **kwargs: Any,
    ) -> BaseMessage:
        """Асинхронный вызов модели"""
        logger.info(f"OllamaModelManager ainvoke [{agent.name}]")
        return await self.get_model(
            model_type=OllamaModel(agent.model),
            temperature=agent.temperature,
            max_tokens=agent.max_tokens,
        ).ainvoke(
            input=input_messages,
            config=config,
            stop=stop,
            **kwargs
        )

    async def ainvoke_with_tools(
            self,
            agent: Agent,
            input_messages: LanguageModelInput,
            config: Optional[RunnableConfig] = None,
            *,
            stop: Optional[list[str]] = None,
            mcp_tools: Optional[Dict[str, Any]] = None,  # Параметр для передачи инструментов MCP
            **kwargs: Any,
    ) -> BaseMessage:
        """Асинхронный вызов модели с передачей инструментов MCP"""
        logger.info(f"OllamaModelManager ainvoke_with_tools [{agent.name}]")
        return await self.get_model(
            model_type=OllamaModel(agent.model),
            temperature=agent.temperature,
            max_tokens=agent.max_tokens,
            mcp_tools=mcp_tools,  # Передаем инструменты в вызов модели
        ).ainvoke(
            input=input_messages,
            config=config,
            stop=stop,
            **kwargs
        )


# Singleton pattern
_ollama_manager: Optional[OllamaModelManager] = None


def get_ollama_manager() -> OllamaModelManager:
    global _ollama_manager
    if _ollama_manager is None:
        _ollama_manager = OllamaModelManager()
    return _ollama_manager


def setup_ollama_manager(base_url: str) -> OllamaModelManager:
    manager = get_ollama_manager()
    manager.base_url = base_url
    return manager
