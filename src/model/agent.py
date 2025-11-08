import uuid
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field

from src.ai.agents_systems import AgentsSystem
from src.model.giga_chat_models import GigaChatModel


class Agent(BaseModel):
    agent_id: str = Field(..., description="ID агента")
    name: str = Field(..., description="Имя агента")
    temperature: float = Field(..., description="Температура агента")
    model: GigaChatModel = Field(..., description="Модель для агента")
    system_prompt: str = Field(..., description="Системный промпт для агента")
    max_tokens: Optional[int] = Field(..., description="Максимальное колличество токенов с которыми работает агент")


class AgentsSystemListResponse(BaseModel):
    systems: List[AgentsSystem] =  Field(..., description="Список агентных систем")

class AgentsSystemRequest(BaseModel):
    system: AgentsSystem =  Field(..., description="Aгентная система пользователя")
