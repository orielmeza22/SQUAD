"""OpenAI LLM provider."""

import json
import urllib.request
from typing import Optional, List, Dict, Any

from .base import LLMProvider


class OpenAIProvider(LLMProvider):
    """Provider for OpenAI API.
    
    Supports chat completions with optional JSON output format.
    """
    
    def __init__(self, api_key: str):
        """Initialize the OpenAI provider.
        
        Args:
            api_key: OpenAI API key.
        """
        self.api_key = api_key
        self.base_url = "https://api.openai.com/v1/chat/completions"
    
    @property
    def provider_name(self) -> str:
        return "OpenAI"
    
    def is_available(self) -> bool:
        """Check if OpenAI API key is configured."""
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
        """Generate text using OpenAI API.
        
        Args:
            model: Model identifier (e.g., 'gpt-4o', 'gpt-4o-mini').
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
            raise Exception("OPENAI_API_KEY no configurada. Añádela a tu archivo .env o .env.local")
        
        # Build messages array
        openai_messages = []
        if prompt:
            openai_messages.append({"role": "user", "content": prompt})
        elif messages:
            for msg in messages:
                openai_messages.append({
                    "role": msg.get("role"),
                    "content": msg.get("content")
                })
        
        payload = {
            "model": model,
            "messages": openai_messages,
            "temperature": temperature
        }
        
        if is_json:
            payload["response_format"] = {"type": "json_object"}
        
        # Make API request
        req = urllib.request.Request(
            self.base_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }
        )
        
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                res = json.loads(response.read().decode('utf-8'))
                
                if 'choices' in res and res['choices']:
                    return res['choices'][0]['message']['content']
                
                raise Exception("Respuesta vacía o incorrecta de OpenAI API")
                
        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8')
            raise Exception(f"OpenAI API Error {e.code}: {err_body}")
