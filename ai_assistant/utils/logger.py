import logging
import time
from typing import Any, Optional

logger = logging.getLogger("ai_assistant")

class AILogger:
    """
    Utility class for structured logging of all AI queries, provider details, and API latency.
    Ensures absolute privacy by NEVER logging raw API keys.
    """

    @staticmethod
    def log_request(
        user: str,
        provider: str,
        prompt_size: int,
        execution_time_ms: int,
        error: Optional[str] = None
    ) -> None:
        """
        Write a structured log entry for the AI query.
        """
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        status = "SUCCESS" if not error else "ERROR"
        
        log_message = (
            f"[{timestamp}] [AI REQUEST] | User: {user} | Provider: {provider} | "
            f"Prompt Size: {prompt_size} chars | Duration: {execution_time_ms}ms | "
            f"Status: {status}"
        )
        
        if error:
            log_message += f" | Details: {error}"
            logger.error(log_message)
        else:
            logger.info(log_message)

        # Also write to custom file inside app data / workspace for audit logs persistence
        try:
            import os
            # Ensure folder exists
            log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, "ai_transactions.log")
            
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(log_message + "\n")
        except Exception:
            pass # Gracefully proceed if filesystem logs are write-blocked
