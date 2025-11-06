import logging
from typing import List, Dict

from langchain_core.messages import BaseMessage
from typing_extensions import override

from src.config.constants import (
    AgentType,
    GigaChatModel,
    HELLO_PROMPT,
)
from src.gigachat_client.base_agent import AgentBase

logger = logging.getLogger(__name__)


class AgentMain(AgentBase):
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

    @override
    def build_messages(
            self,
            question: str = "",
            history: List[Dict[str, str]] = None,
            additionally: Dict[str, str] = None
    ) -> BaseMessage:
        logger.info(f"build_messages = {question}")
        return super().build_messages(
            question=question,
            history=history,
            additionally=additionally,
        )
