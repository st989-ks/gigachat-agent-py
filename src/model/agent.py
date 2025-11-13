from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field

class AgentsSystem(str, Enum):
    DEFAULT = "DEFAULT"
    TECHNICAL_SPECIFICATION = "TECHNICAL_SPECIFICATION"
    COMPARE_ANSWERS = "COMPARE_ANSWERS"
    SUMMARY_DIALOG = "SUMMARY_DIALOG"

class Agent(BaseModel):
    agent_id: str = Field(..., description="ID агента")
    provider: str = Field(..., description="Вид LLM")
    name: str = Field(..., description="Имя агента")
    temperature: float = Field(..., description="Температура агента")
    model: str = Field(..., description="Модель для агента")
    system_prompt: str = Field(..., description="Системный промпт для агента")
    max_tokens: Optional[int] = Field(..., description="Максимальное колличество токенов с которыми работает агент")


class AgentsSystemListResponse(BaseModel):
    systems: List[AgentsSystem] =  Field(..., description="Список агентных систем")

class AgentsSystemRequest(BaseModel):
    system: AgentsSystem =  Field(..., description="Aгентная система пользователя")
