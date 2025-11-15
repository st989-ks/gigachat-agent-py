from pydantic import BaseModel, Field


class StandardResponse(BaseModel):
    message: str = Field(..., description="Answer to the user's request")
    success: bool = Field(default=True, description="Whether the request was fully executed")
