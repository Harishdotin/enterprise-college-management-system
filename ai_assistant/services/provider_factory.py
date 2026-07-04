import os
from typing import Optional
from ai_assistant.providers.base_provider import BaseAIProvider
from ai_assistant.providers.openai_provider import OpenAIProvider
from ai_assistant.providers.gemini_provider import GeminiProvider
from ai_assistant.providers.ollama_provider import OllamaProvider

class AIProviderFactory:
    """
    Factory class to instantiate and return the correct AI Provider
    based on the AI_PROVIDER environment variable.
    """

    @staticmethod
    def get_provider(provider_name: Optional[str] = None) -> BaseAIProvider:
        """
        Instantiate the provider based on current environment variable configuration.
        """
        provider = provider_name or os.getenv("AI_PROVIDER", "GEMINI").upper()

        if provider == "OPENAI":
            api_key = os.getenv("OPENAI_API_KEY", "")
            if not api_key:
                raise ValueError("OpenAI provider selected, but OPENAI_API_KEY is not configured in the environment variables.")
            return OpenAIProvider(api_key=api_key)

        elif provider == "GEMINI":
            api_key = os.getenv("GEMINI_API_KEY", "")
            if not api_key:
                raise ValueError("Gemini provider selected, but GEMINI_API_KEY is not configured in the environment variables.")
            return GeminiProvider(api_key=api_key)

        elif provider == "OLLAMA":
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            return OllamaProvider(base_url=base_url)

        else:
            raise ValueError(f"Invalid AI provider name: '{provider}'. Supported providers are: OPENAI, GEMINI, OLLAMA.")
