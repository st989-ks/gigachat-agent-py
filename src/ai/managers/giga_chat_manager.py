import logging
from typing import Dict, Optional, Tuple, Final, Any

from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableConfig

from src.model.agent import Agent
from src.model.chat_models import GigaChatModel
from langchain_gigachat.chat_models import GigaChat

logger = logging.getLogger(__name__)


class GigaChatModelManager:
    DEFAULT_TEMPERATURE: Final[float] = 0.7
    DEFAULT_STREAMING: Final[bool] = False
    DEFAULT_MAX_TOKENS: Final[int] = 8000
    DEFAULT_TIMEOUT: Final[float] = 300

    def __init__(
            self,
            credentials: str,
            verify_ssl_certs: bool = False
    ):
        self.credentials: str = credentials
        self.verify_ssl_certs: bool = verify_ssl_certs
        self.scope = "GIGACHAT_API_PERS"
        self._models: Dict[
            Tuple[
                GigaChatModel,
                Optional[float],
                bool,
                Optional[int],
                Optional[float]
            ],
            GigaChat
        ] = {}

        self._last_params: Dict[
            GigaChatModel,
            Tuple[Optional[float],
            bool,
            Optional[int],
            Optional[float]]
        ] = {}

        logger.info("GigaChatModelManager init")

    def get_model(
            self,
            model_type: GigaChatModel,
            temperature: Optional[float] = None,
            streaming: Optional[bool] = None,
            max_tokens: Optional[int] = None,
            timeout: Optional[float] = None,
    ) -> GigaChat:

        if model_type in self._last_params:
            last_temp, last_streaming, last_max_tokens, last_timeout = self._last_params[model_type]
        else:
            last_temp = self.DEFAULT_TEMPERATURE
            last_streaming = self.DEFAULT_STREAMING
            last_max_tokens = self.DEFAULT_MAX_TOKENS
            last_timeout = self.DEFAULT_TIMEOUT

        if temperature is None:
            temperature = last_temp

        if streaming is None:
            streaming = last_streaming

        if max_tokens is None:
            max_tokens = last_max_tokens

        if timeout is None:
            timeout = last_timeout

        cache_key = (model_type, temperature, streaming, max_tokens, timeout)
        if cache_key not in self._models:
            self._models[cache_key] = GigaChat(
                credentials=self.credentials,
                scope=self.scope,
                model=model_type.value,
                verify_ssl_certs=self.verify_ssl_certs,
                streaming=streaming,
                max_tokens=max_tokens,
                timeout=timeout,
                temperature=temperature
            )
            logger.info(f"[GigaChatManager] Создана новая модель: {model_type.value}")
        self._last_params[model_type] = (temperature, streaming, max_tokens, timeout)
        return self._models[cache_key]

    def standard(
            self,
            temperature: Optional[float] = None,
            streaming: Optional[bool] = None,
            max_tokens: Optional[int] = None,
            timeout: Optional[float] = None,
    ) -> GigaChat:
        return self.get_model(
            model_type=GigaChatModel.STANDARD,
            temperature=temperature,
            streaming=streaming,
            max_tokens=max_tokens,
            timeout=timeout
        )

    def pro(
            self,
            temperature: Optional[float] = None,
            streaming: Optional[bool] = None,
            max_tokens: Optional[int] = None,
            timeout: Optional[float] = None,
    ) -> GigaChat:
        return self.get_model(
            model_type=GigaChatModel.PRO,
            temperature=temperature,
            streaming=streaming,
            max_tokens=max_tokens,
            timeout=timeout
        )

    def max(
            self,
            temperature: Optional[float] = None,
            streaming: Optional[bool] = None,
            max_tokens: Optional[int] = None,
            timeout: Optional[float] = None,
    ) -> GigaChat:
        return self.get_model(
            model_type=GigaChatModel.MAX,
            temperature=temperature,
            streaming=streaming,
            max_tokens=max_tokens,
            timeout=timeout
        )

    def invoke(
            self,
            agent: Agent,
            input_messages: LanguageModelInput,
            config: Optional[RunnableConfig] = None,
            *,
            stop: Optional[list[str]] = None,
            **kwargs: Any,
    ) -> BaseMessage:
        logger.info(f"GigaChatModelManager invoke [{agent.name}]")
        return self.get_model(
            model_type=agent.model,
            temperature=agent.temperature,
            max_tokens=agent.max_tokens,
        ).invoke(
            input=input_messages,
            config=config,
            stop=stop,
            **kwargs
        )

_ai_model_manager: Optional[GigaChatModelManager] = None

def get_ai_manager() -> GigaChatModelManager:
    global _ai_model_manager
    if _ai_model_manager is None:
        _ai_model_manager = GigaChatModelManager("")
    return _ai_model_manager

def setup_ai_manager(
        credentials: str,
        verify_ssl_certs: bool
) -> GigaChatModelManager:
    manager = get_ai_manager()
    manager.credentials = credentials
    manager.verify_ssl_certs = verify_ssl_certs
    return manager


