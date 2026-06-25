"""Google Gemini LLM provider."""

import json
import urllib.request
from typing import Optional, List, Dict, Any

from .base import LLMProvider


class GeminiProvider(LLMProvider):
    """Provider for Google Gemini API.
    
    Supports both simple prompts and multi-turn conversations with system instructions.
    """
    
    def __init__(self, api_key: str):
        """Initialize the Gemini provider.
        
        Args:
            api_key: Google Gemini API key.
        """
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
    
    @property
    def provider_name(self) -> str:
        return "Gemini"
    
    def is_available(self) -> bool:
        """Check if Gemini API key is configured."""
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
        """Generate text using Gemini API.
        
        Args:
            model: Model identifier (e.g., 'gemini-2.5-flash').
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
            raise Exception("GEMINI_API_KEY no configurada. Añádela a tu archivo .env o .env.local")
        
        contents = []
        system_instruction = None
        
        # Build request payload
        if prompt:
            contents.append({
                "role": "user",
                "parts": [{"text": prompt}]
            })
        elif messages:
            for msg in messages:
                role = msg.get("role")
                content = msg.get("content")
                
                if role == "system":
                    system_instruction = {"parts": [{"text": content}]}
                else:
                    gemini_role = "user" if role == "user" else "model"
                    contents.append({
                        "role": gemini_role,
                        "parts": [{"text": content}]
                    })
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature
            }
        }
        
        if system_instruction:
            payload["systemInstruction"] = system_instruction
        
        if is_json:
            payload["generationConfig"]["responseMimeType"] = "application/json"
        
        # Make API request
        url = f"{self.base_url}/{model}:generateContent?key={self.api_key}"
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                res = json.loads(response.read().decode('utf-8'))
                
                # Validate response structure
                if 'candidates' in res and res['candidates']:
                    candidate = res['candidates'][0]
                    if 'content' in candidate and 'parts' in candidate['content'] and candidate['content']['parts']:
                        return candidate['content']['parts'][0]['text']
                
                raise Exception("Respuesta vacía o estructurada incorrectamente por Gemini API")
                
        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8')
            raise Exception(f"Gemini API Error {e.code}: {err_body}")
