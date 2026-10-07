from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="User message",
    )


class SourceReference(BaseModel):
    source_number: int
    document_id: str
    chunk_index: int
    score: float


class ChatResponse(BaseModel):
    response: str
    model: str

    iterations: int = 1

    rag_used: bool = False
    retrieved_chunks: int = 0

    sources: list[
        SourceReference
    ] = Field(
        default_factory=list
    )

    tools_used: list[str] = Field(
        default_factory=list
    )

    tool_count: int = 0