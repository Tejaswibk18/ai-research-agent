from google import genai

from app.config import get_settings


class LLMService:

    def __init__(self):
        self.settings = get_settings()

        self.client = genai.Client(
            api_key=self.settings.GEMINI_API_KEY
        )

    async def generate_response(self, message: str) -> str:

        response = await self.client.aio.models.generate_content(
            model=self.settings.GEMINI_MODEL,
            contents=message,
        )

        if not response.text:
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        return response.text