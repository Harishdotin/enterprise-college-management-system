import os
import requests
from typing import Any, List, Dict, Optional
from .base_provider import BaseAIProvider

class OllamaProvider(BaseAIProvider):
    """
    Ollama Provider implementation for local models supporting conversation history.
    """

    def __init__(self, base_url: str = None) -> None:
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model_name = os.getenv("OLLAMA_MODEL_NAME", "llama3")

    def generate_response(
        self, 
        prompt: str, 
        history: Optional[List[Dict[str, str]]] = None, 
        system_instruction: Optional[str] = None,
        **kwargs: Any
    ) -> str:
        """
        Send a chat completion request to the local Ollama API server.
        """
        url = f"{self.base_url.rstrip('/')}/api/chat"
        headers = {
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
            "stream": False,
            "options": {
                "temperature": float(temp)
            }
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=45)
            response.raise_for_status()
            res_json = response.json()
            return res_json["message"]["content"]
            
        except requests.exceptions.Timeout:
            raise TimeoutError("Ollama local connection timed out.")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Ollama local connection failed. Check if server is running at {self.base_url}: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Ollama execution error: {str(e)}")
