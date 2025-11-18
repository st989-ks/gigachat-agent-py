import logging
import time
from typing import Dict, Optional, Tuple, Final, Any, List, Sequence

from gigachat.models import TokensCount
from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.prompt_values import PromptValue
from langchain_core.runnables import RunnableConfig

from src.model.agent import Agent
from src.model.chat_models import GigaChatModel
from langchain_gigachat.chat_models import GigaChat
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import Connection
from langgraph.prebuilt import create_react_agent


from src.model.messages import MessageOutput

logger = logging.getLogger(__name__)


class GigaChatModelManager:
    DEFAULT_TEMPERATURE: Final[float] = 0.7
    DEFAULT_STREAMING: Final[bool] = False
    DEFAULT_MAX_TOKENS: Final[int] = 8000
    DEFAULT_TIMEOUT: Final[float] = 300
    COST_TOKEN: Final[float] = 1000 / 5000000
    COST_TOKEN_PRO: Final[float] = 1500 / 1000000
    COST_TOKEN_MAX: Final[float] = 1950 / 1000000

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

    def invoke(
            self,
            agent: Agent,
            input_messages: LanguageModelInput,
            config: Optional[RunnableConfig] = None,
            *,
            stop: Optional[list[str]] = None,
            **kwargs: Any,
    ) -> MessageOutput:
        logger.info(f"GigaChatModelManager invoke [{agent.name}]")
        model = self.get_model(
            model_type=GigaChatModel(agent.model),
            temperature=agent.temperature,
            max_tokens=agent.max_tokens,
        )

        try:
            token_counts_send: list[TokensCount] = model.tokens_count(
                input_=self.extract_text_list(input_messages),
                model=agent.model
            )
        except Exception as e:
            logger.error(e)
            token_counts_send = []
        total_token_counts_send: int = sum(tc.tokens for tc in token_counts_send)

        start_time: float = time.time()
        response: BaseMessage = model.invoke(
            input=input_messages,
            config=config,
            stop=stop,
            **kwargs
        )
        response_time: float = time.time() - start_time

        try:
            token_count_accepted: list[TokensCount] = model.tokens_count(
                input_=self.extract_text_list([response]),
                model=agent.model
            )
        except Exception as e:
            logger.error(e)
            token_count_accepted = []

        total_token_counts_accepted: int = sum(tc.tokens for tc in token_count_accepted)
        response_metadata = response.response_metadata.get('token_usage', {})
        prompt_tokens = response_metadata.get('prompt_tokens', 0)
        completion_tokens = response_metadata.get('completion_tokens', 0)

        if agent.model == GigaChatModel.MAX.value:
            price = self.COST_TOKEN_MAX * (prompt_tokens + completion_tokens)
        elif agent.model == GigaChatModel.PRO.value:
            price = self.COST_TOKEN_PRO * (prompt_tokens + completion_tokens)
        else:
            price = self.COST_TOKEN * (prompt_tokens + completion_tokens)

        return MessageOutput(
            message=response,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            request_time=response_time,
            price=price,
            meta=(
                f"Локальный расчет токенов (send) {str(total_token_counts_send)}\n"
                f"Локальный расчет токенов (accepted) {str(total_token_counts_accepted)}\n"
            )
        )

    async def invoke_with_tools(
            self,
            connections: dict[str, Connection],
            agent: Agent,
            input_messages: LanguageModelInput,
    ) -> MessageOutput:
        logger.info("GigaChatModelManager invoke with tools")

        model = self.get_model(
            model_type=GigaChatModel(agent.model),
            temperature=agent.temperature,
            max_tokens=agent.max_tokens,
        )

        start_time: float = time.time()

        client = MultiServerMCPClient(connections=connections)

        tools = await client.get_tools()
        
        react_agent = create_react_agent(model, tools)

        agent_output:dict = await react_agent.ainvoke(input={"messages": input_messages})
        logger.info(f"[agent_output] {agent_output}")
        response: BaseMessage = agent_output["messages"][-1] 

        response_time: float = time.time() - start_time
        response_metadata = response.response_metadata.get('token_usage', {})
        prompt_tokens = response_metadata.get('prompt_tokens', 0)
        completion_tokens = response_metadata.get('completion_tokens', 0)
        if agent.model == GigaChatModel.MAX.value:
            price = self.COST_TOKEN_MAX * (prompt_tokens + completion_tokens)
        elif agent.model == GigaChatModel.PRO.value:
            price = self.COST_TOKEN_PRO * (prompt_tokens + completion_tokens)
        else:
            price = self.COST_TOKEN * (prompt_tokens + completion_tokens)
        return MessageOutput(
            message=response,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            request_time=response_time,
            price=price,
            meta="Agent with MCP tools invoked"
        )

    @staticmethod
    def extract_text_list(input_data: LanguageModelInput) -> List[str]:
        if isinstance(input_data, str):
            return [input_data]

        if isinstance(input_data, PromptValue):
            return [input_data.to_string()]

        if isinstance(input_data, Sequence):
            return [
                msg.content if hasattr(msg, "content") # type: ignore
                else msg.get("content", str(msg)) if isinstance(msg, dict)
                else str(msg)
                for msg in input_data
            ]

        return [str(input_data)]


_ai_model_manager: Optional[GigaChatModelManager] = None


def get_giga_chat_manager() -> GigaChatModelManager:
    global _ai_model_manager
    if _ai_model_manager is None:
        _ai_model_manager = GigaChatModelManager("")
    return _ai_model_manager


def setup_giga_chat_manager(
        credentials: str,
        verify_ssl_certs: bool
) -> GigaChatModelManager:
    manager = get_giga_chat_manager()
    manager.credentials = credentials
    manager.verify_ssl_certs = verify_ssl_certs
    return manager
