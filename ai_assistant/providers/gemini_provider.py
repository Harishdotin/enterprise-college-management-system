import os
from typing import Any, List, Dict, Optional
from google import genai
from .base_provider import BaseAIProvider


class GeminiProvider(BaseAIProvider):
    

    print("GEMINI_API_KEY exists:", bool(os.getenv("GEMINI_API_KEY")))
    print("GEMINI_API_KEY length:", len(os.getenv("GEMINI_API_KEY", "AQ.AxxxxxIsoXxxxxxfT3O1NXgzxxxxxFdaauH9UvAba2ff-xxxxx")))

    def __init__(self, api_key: str = None) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash")

        if not self.api_key:
            raise ValueError("Gemini API key is missing.")

        self.client = genai.Client(api_key=self.api_key)

    def generate_response(
        self,
        prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
        system_instruction: Optional[str] = None,
        **kwargs: Any
    ) -> str:

        try:
            full_prompt = ""

            if system_instruction:
                full_prompt += f"System:\n{system_instruction}\n\n"

            if history:
                for msg in history[-8:]:
                    full_prompt += f"{msg['role']}: {msg['message']}\n"

            full_prompt += f"\nUser: {prompt}"

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt
            )

            return response.text

        except Exception as e:
            raise RuntimeError(f"Gemini API Error: {e}")