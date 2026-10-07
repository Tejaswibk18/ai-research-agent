from typing import Any

from pydantic import BaseModel, Field


class ToolExecution(BaseModel):
    tool_name: str
    arguments: dict[str, Any] = Field(
        default_factory=dict
    )
    result: Any = None
    success: bool = True


class AgentExecution(BaseModel):
    iterations: int = 0
    tools_used: list[str] = Field(
        default_factory=list
    )
    tool_calls: list[ToolExecution] = Field(
        default_factory=list
    )
    sources: list[dict[str, Any]] = Field(
        default_factory=list
    )
    final_response: str = ""


class AgentResponse(BaseModel):
    response: str
    model: str

    iterations: int
    tools_used: list[str]
    tool_count: int

    rag_used: bool
    retrieved_chunks: int

    sources: list[dict[str, Any]]