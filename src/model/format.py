from typing import List

from pydantic import BaseModel, Field

from src.model.tape_formats_response import FormatType


class FormatTypeListResponse(BaseModel):
    formats: List[FormatType] = Field(..., description="Список способов ответа")


class FormatTypeRequest(BaseModel):
    format_type: FormatType = Field(..., description="Формат ответа АИ")
    format: str = Field(..., description="Структура ответа")
