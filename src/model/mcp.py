from pydantic import BaseModel, Field


class MCPTool(BaseModel):
    name: str = Field(..., description="Имя инструмента")
    description: str = Field(..., description="Описание инструмента")
    input_schema: dict = Field(..., description="JSON схема входных параметров инструмента")


class MCPServer(BaseModel):
    name: str = Field(..., description="Название сервера")
    version: str = Field(..., description="Версия протокола")
    tools: list[MCPTool] = Field(..., description="Список доступных инструментов")
