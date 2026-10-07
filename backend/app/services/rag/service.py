from google import genai

from app.config import get_settings
from app.services.document.indexer import DocumentIndexer


class RAGService:
    def __init__(self):
        self.settings = get_settings()

        self.client = genai.Client(
            api_key=self.settings.GEMINI_API_KEY
        )

        self.indexer = DocumentIndexer()

    async def retrieve(
        self,
        query: str
    ) -> list[dict]:

        return await self.indexer.search(
            query=query,
            top_k=self.settings.RAG_TOP_K,
            similarity_threshold=(
                self.settings.RAG_SIMILARITY_THRESHOLD
            ),
        )

    def build_context(
        self,
        results: list[dict]
    ) -> str:

        if not results:
            return ""

        context_parts = []

        for position, result in enumerate(
            results,
            start=1
        ):
            context_parts.append(
                f"""
SOURCE {position}
Document ID: {result["document_id"]}
Chunk: {result["chunk_index"]}
Similarity: {result["score"]}

Content:
{result["text"]}
""".strip()
            )

        return "\n\n---\n\n".join(
            context_parts
        )

    def build_prompt(
        self,
        question: str,
        context: str
    ) -> str:

        return f"""
You are the AI Research Agent.

Answer the user's question using the provided
knowledge-base context.

IMPORTANT RULES:

1. Use the supplied context as the primary source
   of truth when answering document-related questions.

2. Do not invent facts that are not supported
   by the context.

3. If the context does not contain enough information,
   clearly say that the uploaded documents do not
   provide enough information.

4. You may use your general knowledge for conversational
   questions, but do not pretend that general knowledge
   came from the uploaded documents.

5. When using information from the context, reference
   the relevant source number such as [Source 1].

6. Give a clear and useful answer.

KNOWLEDGE BASE CONTEXT:

{context if context else "No relevant knowledge-base content was found."}

USER QUESTION:

{question}
""".strip()

    async def generate_response(
        self,
        question: str
    ) -> dict:

        results = await self.retrieve(
            question
        )

        context = self.build_context(
            results
        )

        prompt = self.build_prompt(
            question,
            context
        )

        response = await self.client.aio.models.generate_content(
            model=self.settings.GEMINI_MODEL,
            contents=prompt,
        )

        if not response.text:
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        sources = [
            {
                "source_number": index,
                "document_id": result["document_id"],
                "chunk_index": result["chunk_index"],
                "score": result["score"],
            }
            for index, result in enumerate(
                results,
                start=1
            )
        ]

        return {
            "response": response.text,
            "sources": sources,
            "retrieved_chunks": len(results),
            "rag_used": bool(results),
        }