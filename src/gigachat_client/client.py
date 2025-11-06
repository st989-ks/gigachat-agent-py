import logging
from typing import List, Dict, Optional

from langchain_core.messages import BaseMessage

from src.gigachat_client.catalog_agents import AgentBase, get_catalog

logger = logging.getLogger(__name__)

class GigaChatClient:
    """
        Клиент для работы с GigaChat API через LangChain.
    """

    def __init__(
            self,
            agent: AgentBase = get_catalog().get_agent_by_key(agent_key="main")
    ):
        self._agent = agent

    def set_temperature(self, temperature: float) -> Optional[BaseMessage]:
        self._agent.temperature = temperature
        logger.info(f"set_temperature = {temperature}")
        return self._agent.create_llm()

    def set_agent(self, agent: AgentBase) -> Optional[BaseMessage]:
        self._agent = agent
        logger.info(f"set_agent = {agent.name}")
        return self._agent.create_llm()

    def get_current_agent(self) -> AgentBase:
        return self._agent

    def chat(
            self,
            question: str = "",
            history: List[Dict[str, str]] = None,
            additionally: Dict[str, str] = None
    ) -> str:
        response = self._agent.build_messages(
            question=question,
            history=history,
            additionally=additionally
        )

        return response.content
