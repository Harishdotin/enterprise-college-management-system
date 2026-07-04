from typing import Union

def validate_prompt(prompt: Union[str, None], max_length: int = 4000) -> None:
    """
    Validate that the prompt is not empty, is a valid string, and does not exceed max length.
    
    :param prompt: The input prompt string.
    :param max_length: Maximum allowed character length.
    :raises ValueError: If prompt is invalid or exceeds max length.
    """
    if not prompt or not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("Prompt cannot be empty.")
        
    if len(prompt) > max_length:
        raise ValueError(f"Prompt exceeds the maximum allowed length of {max_length} characters (Current length: {len(prompt)}).")
