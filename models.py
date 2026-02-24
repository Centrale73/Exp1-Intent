import os
from typing import Optional
from agno.models.base import Model
from agno.models.openai import OpenAIChat
from agno.models.anthropic import Anthropic
from agno.models.perplexity import Perplexity

def get_model(provider: str = "perplexity", model_id: Optional[str] = None) -> Model:
    """
    Factory to create an Agno model instance based on provider name.
    """
    provider = provider.lower()
    
    if provider == "openai":
        return OpenAIChat(id=model_id or "gpt-4o")
    elif provider == "anthropic":
        return Anthropic(id=model_id or "claude-3-5-sonnet-20240620")
    elif provider == "perplexity":
        return Perplexity(id=model_id or "sonar-pro")
    else:
        raise ValueError(f"Unsupported provider: {provider}")
