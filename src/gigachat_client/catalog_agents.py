"""
Модуль агентов - управление агентами и их выполнение.
"""

import logging
from typing import Any, Dict, List, Optional

from src.config.constants import (
    DEFAULT_AGENT_TEMPERATURE,
    DEFAULT_AGENT_MODEL,
    DEFAULT_AGENT_MAX_CONTEXT,
    DEFAULT_AGENT_MAX_TOKENS,
    DEFAULT_SYSTEM_PROMPT,
    DEFAULT_AGENT_NAME,
    DEFAULT_AGENT_TYPE,
    HELLO_PROMPT,
)
from src.gigachat_client.agent_formatter import AgentFormatter
from src.gigachat_client.agent_main import AgentMain
from src.gigachat_client.base_agent import AgentBase
from src.gigachat_client.agent_tech_spec import TechnicalSpecificationAgent

logger = logging.getLogger(__name__)


class AgentCatalog:
    """
        Каталог и фабрика агентов.
    """

    _agents: Dict[str, AgentBase] = {}

    def __init__(self) -> None:
        """Инициализирует каталог."""
        self._agents = {}
        self._register_predefined_agents()

    def _register_predefined_agents(self) -> None:
        """Регистрирует предопределенные агенты."""
        self._agents = {
            "main": AgentMain(),
            "formater": AgentFormatter(),
            "tech_spec": TechnicalSpecificationAgent(),
        }
        for agent in self._agents.values():
            logger.info(f"Agent created: {agent.name} (ID: {agent.id})")

    def create_agent(self, spec: Dict[str, Any]) -> AgentBase:
        agent = AgentBase(
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

    def get_agent_by_key(self, agent_key: str) -> Optional[AgentBase]:
        """Получает агента по Ключу."""
        return self._agents.get(agent_key)

    def list_available_agents(self) -> List[AgentBase]:
        """Возвращает список всех доступных агентов."""
        return list(self._agents.values())


_catalog = None


def get_catalog() -> AgentCatalog:
    """Получить глобальный каталог агентов."""
    global _catalog
    if _catalog is None:
        _catalog = AgentCatalog()
    return _catalog
