import os
import requests
from typing import Any, List, Dict, Optional
from .base_provider import BaseAIProvider

class OpenAIProvider(BaseAIProvider):
    """
    OpenAI API Provider implementation supporting conversation history.
    """

    def __init__(self, api_key: str = None) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")

    def generate_response(
        self, 
        prompt: str, 
        history: Optional[List[Dict[str, str]]] = None, 
        system_instruction: Optional[str] = None,
        **kwargs: Any
    ) -> str:
        """
        Send the prompt request with system instructions and chat history to OpenAI chat completions.
        """
        if not self.api_key:
            raise ValueError("OpenAI API key is missing. Configure OPENAI_API_KEY in .env.")

        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Build message history context payload
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        
        if history:
            # Limit history context size for performance
            for h in history[-8:]:
                role = "assistant" if h["role"] == "assistant" else "user"
                messages.append({"role": role, "content": h["message"]})
                
        messages.append({"role": "user", "content": prompt})

        temp = kwargs.get("temperature", 0.7)
        data = {
            "model": self.model_name,
            "messages": messages,
            "temperature": float(temp)
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            if response.status_code == 401:
                raise ValueError("Invalid OpenAI API key.")
            elif response.status_code == 429:
                raise RuntimeError("OpenAI rate limit / quota exceeded.")
            
            response.raise_for_status()
            res_json = response.json()
            return res_json["choices"][0]["message"]["content"]
            
        except requests.exceptions.Timeout:
            raise TimeoutError("OpenAI request timed out.")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"OpenAI API network failure: {str(e)}")
        except Exception as e:
            if isinstance(e, ValueError):
                raise e
            raise RuntimeError(f"OpenAI request error: {str(e)}")
