import os

from dotenv import load_dotenv
from google import genai


load_dotenv()


class LLMService:

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is not configured."
            )

        self.client = genai.Client(api_key=api_key)

        self.model = "gemini-3.5-flash-lite"

    def generate(self, messages: list[dict]) -> str:

        prompt_parts = []

        for message in messages:
            role = message["role"]
            content = message["content"]

            prompt_parts.append(
                f"{role.upper()}:\n{content}"
            )

        prompt = "\n\n".join(prompt_parts)

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
        )

        return response.text