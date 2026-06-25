"""Base interface for LLM providers."""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any


class LLMProvider(ABC):
    """Abstract base class for all LLM providers.
    
    All provider implementations must inherit from this class and implement
    the required methods. This ensures a consistent interface across different
    LLM backends (Ollama, Gemini, OpenAI, etc.).
    """
    
    @abstractmethod
    def generate(
        self,
        model: str,
        prompt: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        is_json: bool = False,
        temperature: float = 0.3,
        **kwargs: Any
    ) -> str:
        """Generate text using the specified model.
        
        Args:
            model: The model identifier to use for generation.
            prompt: A simple prompt string (alternative to messages).
            messages: A list of message dictionaries with 'role' and 'content'.
            is_json: If True, request JSON-formatted output.
            temperature: Sampling temperature (0.0 to 2.0).
            **kwargs: Additional provider-specific parameters.
            
        Returns:
            The generated text response.
            
        Raises:
            Exception: If the API call fails or returns an invalid response.
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is available and properly configured.
        
        Returns:
            True if the provider can be used, False otherwise.
        """
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of this provider."""
        pass
