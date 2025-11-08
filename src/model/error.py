from typing import Optional

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    message: str = Field(..., description="Сообщение об ошибке для глаз человека :)")
    type: str = Field(..., description="Тип ошибки")
    param: Optional[str] = Field(
        None, description="Параметр, вызвавший ошибку"
    )
    code: str = Field(..., description="Сообщение об ошибке для системы")

class ErrorResponse(BaseModel):
    error: ErrorDetail = Field(..., description="Детали ошибки")