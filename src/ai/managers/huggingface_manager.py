import logging
import os
from typing import Optional, Any
from huggingface_hub import AsyncInferenceClient
from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from src.model.agent import Agent
from src.model.chat_models import HuggingFaceModel

logger = logging.getLogger(__name__)


class HuggingFaceModelManager:
    """
    Менеджер для работы с HuggingFace Inference API
    Использует AsyncInferenceClient для async операций
    """

    DEFAULT_TEMPERATURE: float = 0.7
    DEFAULT_MAX_TOKENS: int = 512

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("HF_TOKEN")
        if not self.api_key:
            raise ValueError("HF_TOKEN not found in environment or params")

        self.client = AsyncInferenceClient(api_key=self.api_key)
        logger.info("HuggingFaceModelManager init")

    def _messages_to_prompt(self, messages: list[BaseMessage]) -> str:
        """Конвертировать LangChain messages в текстовый промпт"""
        prompt_parts = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                prompt_parts.append(f"System: {msg.content}")
            elif isinstance(msg, HumanMessage):
                prompt_parts.append(f"User: {msg.content}")
            elif isinstance(msg, AIMessage):
                prompt_parts.append(f"Assistant: {msg.content}")
        return "\n".join(prompt_parts)

    async def ainvoke(
            self,
            agent: Agent,
            input_messages: LanguageModelInput,
            config: Optional[RunnableConfig] = None,
            *,
            stop: Optional[list[str]] = None,
            **kwargs: Any,
    ) -> BaseMessage:
        """Асинхронный вызов HuggingFace API"""
        logger.info(f"HuggingFaceModelManager ainvoke [{agent.name}]")

        # Конвертируем messages в prompt
        if isinstance(input_messages, list):
            prompt = self._messages_to_prompt(input_messages)
        else:
            prompt = str(input_messages)

        # Вызов API
        response = await self.client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model=agent.model,
                max_tokens=agent.max_tokens or self.DEFAULT_MAX_TOKENS,
                temperature=agent.temperature,
            )

        return AIMessage(content=response.choices[0].message.content)

# Singleton
_hf_manager: Optional[HuggingFaceModelManager] = None


def get_hf_manager() -> HuggingFaceModelManager:
    global _hf_manager
    if _hf_manager is None:
        _hf_manager = HuggingFaceModelManager()
    return _hf_manager


def setup_hf_manager(api_key: str) -> HuggingFaceModelManager:
    global _hf_manager
    _hf_manager = HuggingFaceModelManager(api_key=api_key)
    return _hf_manager
