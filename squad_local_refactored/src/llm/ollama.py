"""Ollama LLM provider for local model inference."""

import json
import urllib.request
from typing import Optional, List, Dict, Any, Callable

from .base import LLMProvider


class OllamaProvider(LLMProvider):
    """Provider for Ollama local LLM server.
    
    Supports both chat and completion endpoints with optional streaming.
    """
    
    def __init__(self, host: str = "http://127.0.0.1:11434"):
        """Initialize the Ollama provider.
        
        Args:
            host: The URL of the Ollama server (default: http://127.0.0.1:11434).
        """
        self.host = host
    
    @property
    def provider_name(self) -> str:
        return "Ollama"
    
    def is_available(self) -> bool:
        """Check if Ollama server is online and responding."""
        try:
            with urllib.request.urlopen(f"{self.host}/", timeout=2) as response:
                return response.status == 200
        except Exception:
            return False
    
    def list_models(self) -> List[str]:
        """Get list of available models from Ollama (excluding vision/vl models).
        
        Returns:
            List of model names.
        """
        try:
            with urllib.request.urlopen(f"{self.host}/api/tags", timeout=3) as req:
                data = json.loads(req.read().decode('utf-8'))
                raw_list = [model['name'] for model in data.get('models', [])]
                filtered = [m for m in raw_list if "vl" not in m.lower()]
                coder_models = [m for m in filtered if "coder" in m.lower()]
                other_models = [m for m in filtered if "coder" not in m.lower()]
                return coder_models + other_models
        except Exception:
            return []

    
    def generate(
        self,
        model: str,
        prompt: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        is_json: bool = False,
        temperature: float = 0.3,
        num_ctx: int = 16384,
        num_predict: int = 4096,
        stream_callback: Optional[Callable[[str], None]] = None,
        **kwargs: Any
    ) -> str:
        """Generate text using Ollama.
        
        Args:
            model: Model name to use.
            prompt: Simple prompt (for /api/generate endpoint).
            messages: Chat messages (for /api/chat endpoint).
            is_json: Request JSON output format.
            temperature: Sampling temperature.
            num_ctx: Context window size.
            num_predict: Maximum tokens to generate.
            stream_callback: Optional callback for streaming responses.
            
        Returns:
            Generated text.
        """
        payload = {
            "model": model,
            "stream": stream_callback is not None,
            "options": {
                "num_ctx": num_ctx,
                "num_predict": num_predict,
                "temperature": temperature
            }
        }
        
        if prompt:
            payload["prompt"] = prompt
        if messages:
            payload["messages"] = messages
        if is_json:
            payload["format"] = "json"
        
        # Choose endpoint based on input type
        url = f"{self.host}/api/generate" if prompt else f"{self.host}/api/chat"
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        # Handle streaming
        if stream_callback:
            try:
                with urllib.request.urlopen(req, timeout=120) as response:
                    accumulated = []
                    for line in response:
                        if line:
                            chunk = json.loads(line.decode('utf-8'))
                            # Extract text based on endpoint type
                            text = chunk.get('response', '') if prompt else chunk.get('message', {}).get('content', '')
                            accumulated.append(text)
                            stream_callback("".join(accumulated))
                    return "".join(accumulated)
            except Exception as e:
                print(f"[OLLAMA STREAM ERROR] {e}")
                # Fall back to non-streaming
        
        # Non-streaming request
        with urllib.request.urlopen(req, timeout=300) as response:
            res = json.loads(response.read().decode('utf-8'))
            return res.get('response', '') if prompt else res.get('message', {}).get('content', '')
