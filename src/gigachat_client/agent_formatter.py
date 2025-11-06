import logging
from typing import List, Dict, Any

from langchain_core.messages import (
    BaseMessage,
    SystemMessage,
    HumanMessage,
)

from src.config.constants import (
    TAG,
    TagFormatResponse,
    TAG_FORMAT,
    PROMPT_MAP,
    TAG_SYSTEM_PROMPT,
    AgentType,
    GigaChatModel,
)

logger = logging.getLogger(__name__)

from src.gigachat_client.base_agent import AgentBase

class AgentFormatter(AgentBase):

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
                "1. Ответ — Без пояснений, без комментариев, без вводных слов.\n"
                "2. Не добавляй Markdown-подсветку или кавычки.\n"
                "3. Ответ — это ТОЛЬКО тело структуры данных.\n"
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
    ) -> BaseMessage:
        """Формирует минимальный контекст — только системное сообщение и текущий вопрос."""
        logger.info(f"build_messages = {question}")
        if additionally is None:
            additionally = {}
        format_tag = additionally.get(TAG, TagFormatResponse.DEFAULT.value)
        format_structure = additionally.get(TAG_FORMAT, "")

        extra_prompt = PROMPT_MAP.get(format_tag, "")

        system_format_message = SystemMessage(
            content=f"{self.system_prompt}\n\n {extra_prompt} \n\n {format_structure}",
            kwargs={TAG, TAG_SYSTEM_PROMPT}
        )
        logger.info(system_format_message)
        messages: List[Any] = [
            system_format_message,
            HumanMessage(content=question)
        ]
        return self._llm.invoke(messages)
