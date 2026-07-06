import time
import os
from typing import Any, Dict, Optional, List
from accounts.models import User
from ai_assistant.models import AIChatMessage, AIConfiguration
from ai_assistant.utils.validators import validate_prompt
from ai_assistant.utils.logger import AILogger
from .provider_factory import AIProviderFactory
from .prompt_builder import PromptBuilder
from .response_formatter import ResponseFormatter

# Global cache to reuse provider instances across requests (Step 9)
_provider_cache: Dict[str, Any] = {}

class AIService:
    """
    AIService coordinates validators, provider factories, prompts generation,
    history context gathering, execution timers, and logs queries securely.
    """

    def __init__(self, provider_name: Optional[str] = None) -> None:
        self.provider_name = provider_name or os.getenv("AI_PROVIDER", "GEMINI").upper()
        self.prompt_builder = PromptBuilder()
        self.response_formatter = ResponseFormatter()

    def _get_cached_provider(self) -> Any:
        """
        Retrieve provider instance from cache or create a new one. (Step 9)
        """
        cache_key = self.provider_name
        if cache_key not in _provider_cache:
            # Factory handles environment configuration checks
            _provider_cache[cache_key] = AIProviderFactory.get_provider(self.provider_name)
        return _provider_cache[cache_key]

    def process_chat_query(self, user_name: str, raw_prompt: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Validate prompt, pull context history, invoke LLM client, handle errors, and format output.
        """
        start_time = time.time()
        
        # 1. Validation (Step 10 / Step 7 validation checks)
        try:
            validate_prompt(raw_prompt, max_length=500)
        except ValueError as e:
            execution_time = int((time.time() - start_time) * 1000)
            AILogger.log_request(user_name, "VALIDATION", len(raw_prompt or ""), execution_time, str(e))
            return {
                "status": "error",
                "error_type": "VALIDATION_ERROR",
                "message": str(e)
            }

        try:
            # Fetch user context
            user_obj = User.objects.get(username=user_name)
        except User.DoesNotExist:
            return {
                "status": "error",
                "message": "User context not found."
            }

        # 2. Gather conversation history context (Step 7)
        # Limit history context size for performance (last 8 messages)
        history_objs = AIChatMessage.objects.filter(user=user_obj).order_by('-timestamp')[:8]
        history_list = []
        for h in reversed(history_objs):
            history_list.append({
                "role": h.role,
                "message": h.message
            })

        # 3. Load provider instance
        try:
            provider = self._get_cached_provider()
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            AILogger.log_request(user_name, "CONFIG_ERROR", len(raw_prompt), execution_time, str(e))
            return {
                "status": "error",
                "error_type": "CONFIG_ERROR",
                "message": f"AI provider initialization error: {str(e)}"
            }

        # 4. Resolve system instruction prompt (Step 5)
        system_instruction = self.prompt_builder.get_system_prompt(user_obj.role)

        # 5. Call LLM provider (Step 8 error handling)
        try:
            print(kwargs)

            kwargs.pop("system_instruction", None)

            raw_response = provider.generate_response(
                prompt=raw_prompt,
                history=history_list,
                system_instruction=system_instruction,
                **kwargs
            )
            
            execution_time = int((time.time() - start_time) * 1000)
            AILogger.log_request(user_name, self.provider_name, len(raw_prompt), execution_time)
            
            # Format output response (Step 6)
            formatted_text = self.response_formatter.to_markdown(raw_response)
            
            return {
                "status": "success",
                "message": formatted_text,
                "provider": self.provider_name,
                "execution_time_ms": execution_time
            }

        except ValueError as e:
            # Custom API credential issues
            execution_time = int((time.time() - start_time) * 1000)
            AILogger.log_request(user_name, self.provider_name, len(raw_prompt), execution_time, str(e))
            return {
                "status": "error",
                "error_type": "AUTHENTICATION_ERROR",
                "message": "Invalid API key or unauthorized access configured. Verify settings."
            }

        except TimeoutError as e:
            execution_time = int((time.time() - start_time) * 1000)
            AILogger.log_request(user_name, self.provider_name, len(raw_prompt), execution_time, "Timeout")
            return {
                "status": "error",
                "error_type": "TIMEOUT_ERROR",
                "message": "The request to the AI model timed out. Please try again."
            }

        except RuntimeError as e:
            execution_time = int((time.time() - start_time) * 1000)
            error_str = str(e)
            AILogger.log_request(user_name, self.provider_name, len(raw_prompt), execution_time, error_str)
            
            # Check for quota limits
            if "quota" in error_str.lower() or "rate limit" in error_str.lower():
                return {
                    "status": "error",
                    "error_type": "QUOTA_ERROR",
                    "message": "AI usage quota has been exceeded or rate-limited. Please try again shortly."
                }
            return {
                "status": "error",
                "error_type": "PROVIDER_UNAVAILABLE",
                "message": f"AI provider connection issue: {error_str}"
            }

        except Exception as e:
            import traceback
            traceback.print_exc()   # <-- Render logs-la full error varum

            execution_time = int((time.time() - start_time) * 1000)
            AILogger.log_request(
                user_name,
                self.provider_name,
                len(raw_prompt),
                execution_time,
                str(e)
            )
    
            return {
                "status": "error",
                "error_type": "SYSTEM_ERROR",
                "message": str(e)   # Temporary debug
            }