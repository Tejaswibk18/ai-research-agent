from fastapi import APIRouter, HTTPException

from app.models.chat import (
    ChatRequest,
    ChatResponse,
)
from app.config import get_settings
from app.services.tool_agent import (
    agent_service,
)


router = APIRouter(
    prefix="/api/agent",
    tags=["Agent"],
)


settings = get_settings()


@router.post(
    "/run",
    response_model=ChatResponse,
)
async def run_agent(
    request: ChatRequest,
):

    try:

        result = await agent_service.run(
            request.message
        )

        sources = result.get(
            "sources",
            []
        )

        return ChatResponse(
            response=result["response"],
            model=settings.GEMINI_MODEL,

            iterations=result[
                "iterations"
            ],

            tools_used=result[
                "tools_used"
            ],

            tool_count=len(
                result["tool_calls"]
            ),

            rag_used=bool(
                sources
            ),

            retrieved_chunks=len(
                sources
            ),

            sources=[
                {
                    "source_number": index,
                    "document_id": source[
                        "document_id"
                    ],
                    "chunk_index": source[
                        "chunk_index"
                    ],
                    "score": source[
                        "score"
                    ],
                }
                for index, source in enumerate(
                    sources,
                    start=1,
                )
            ],
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Agent execution failed: "
                f"{str(exc)}"
            ),
        )