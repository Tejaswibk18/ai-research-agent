from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routes.chat import router as chat_router
from app.routes.documents import router as documents_router
from app.routes.agent import router as agent_router


settings = get_settings()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "AI Research Agent platform built with Gemini, "
        "RAG, tools, memory, and agents."
    ),
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(chat_router)
app.include_router(documents_router)
app.include_router(agent_router)

@app.get("/")
async def root():
    return {
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy"
    }

