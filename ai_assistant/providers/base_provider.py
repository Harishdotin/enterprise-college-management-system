from abc import ABC, abstractmethod
from typing import Any, List, Dict, Optional

class BaseAIProvider(ABC):
    """
    Abstract Base Class defining the interface/contract for all AI Providers.
    All custom providers (Gemini, OpenAI, Ollama, etc.) must implement this interface.
    """

    @abstractmethod
    def generate_response(
        self, 
        prompt: str, 
        history: Optional[List[Dict[str, str]]] = None, 
        system_instruction: Optional[str] = None,
        **kwargs: Any
    ) -> str:
        """
        Generate a text response based on the prompt, previous history, and system instruction.

        :param prompt: The input query or prompt for the AI model.
        :param history: Optional list of previous chat messages: [{"role": "user"|"assistant", "content": "text"}]
        :param system_instruction: Optional system instruction/persona prompt.
        :param kwargs: Optional parameters (e.g. temperature, max_tokens, etc.)
        :return: The generated string response from the model.
        """
        pass
