"""OpenRouter LLM provider for accessing multiple model providers."""

import json
import urllib.request
from typing import Optional, List, Dict, Any

from .base import LLMProvider


class OpenRouterProvider(LLMProvider):
    """Provider for OpenRouter API.
    
    OpenRouter provides unified access to models from multiple providers.
    """
    
    def __init__(self, api_key: str):
        """Initialize the OpenRouter provider.
        
        Args:
            api_key: OpenRouter API key.
        """
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
    
    @property
    def provider_name(self) -> str:
        return "OpenRouter"
    
    def is_available(self) -> bool:
        """Check if OpenRouter API key is configured."""
        return bool(self.api_key)
    
    def generate(
        self,
        model: str,
        prompt: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        is_json: bool = False,
        temperature: float = 0.3,
        **kwargs: Any
    ) -> str:
        """Generate text using OpenRouter API.
        
        Args:
            model: Model identifier (e.g., 'anthropic/claude-3-opus').
            prompt: Simple prompt string.
            messages: List of message dictionaries with 'role' and 'content'.
            is_json: Request JSON output format.
            temperature: Sampling temperature.
            
        Returns:
            Generated text response.
            
        Raises:
            Exception: If API key is missing or API call fails.
        """
        if not self.api_key:
            raise Exception("OPENROUTER_API_KEY no configurada. Añádela en Ajustes o al archivo .env")
        
        # Build messages array
        openrouter_messages = []
        if prompt:
            openrouter_messages.append({"role": "user", "content": prompt})
        elif messages:
            for msg in messages:
                openrouter_messages.append({
                    "role": msg.get("role"),
                    "content": msg.get("content")
                })
        
        payload = {
            "model": model,
            "messages": openrouter_messages,
            "temperature": temperature
        }
        
        if is_json:
            payload["response_format"] = {"type": "json_object"}
        
        # Make API request with required headers
        req = urllib.request.Request(
            self.base_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}',
                'HTTP-Referer': 'http://localhost:8000',
                'X-Title': 'SQUAD Builder'
            }
        )
        
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                res = json.loads(response.read().decode('utf-8'))
                
                if 'choices' in res and res['choices']:
                    return res['choices'][0]['message']['content']
                
                raise Exception("Respuesta vacía o incorrecta de OpenRouter API")
                
        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8')
            raise Exception(f"OpenRouter API Error {e.code}: {err_body}")
