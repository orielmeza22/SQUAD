"""Unified AI provider with smart routing, fallback, and caching."""

import hashlib
from typing import Optional, List, Dict, Any, Callable

from ..core.config import settings
from ..core.state import state
from .base import LLMProvider
from .ollama import OllamaProvider
from .gemini import GeminiProvider
from .openai import OpenAIProvider
from .openrouter import OpenRouterProvider


def get_fallback_model(ollama_models: List[str]) -> str:
    """Select the best fallback model from available Ollama models.
    
    Prioritizes coder models and smaller models for efficiency.
    """
    coder_models = [m for m in ollama_models if "coder" in m]
    if coder_models:
        # Prefer specific sizes
        for size in ["7b", "8b", "14b", "3b", "1.5b"]:
            match = next((m for m in coder_models if size in m), None)
            if match:
                return match
        return coder_models[0]
    
    # Fallback to general models
    for size in ["3b", "8b", "14b", "7b"]:
        match = next((m for m in ollama_models if size in m), None)
        if match:
            return match
    
    return ollama_models[0] if ollama_models else "llama2"


class AIProvider:
    """Unified provider with smart routing, fallback chains, and caching.
    
    This class implements:
    - Smart model routing based on task type (planning vs generation)
    - Automatic fallback between providers (Gemini → Ollama → OpenAI)
    - Response caching to reduce API calls
    - Token and cost tracking
    """
    
    def __init__(self):
        """Initialize the AI provider with configured backends."""
        self.ollama = OllamaProvider(host=settings.ollama_host)
        self.gemini = GeminiProvider(api_key=settings.gemini_api_key or "")
        self.openai = OpenAIProvider(api_key=settings.openai_api_key or "")
        self.openrouter = OpenRouterProvider(api_key=settings.openrouter_api_key or "")
        
        # Cache file path
        self.cache_file = "llm_cache.json"
    
    def _get_cache_key(self, model: str, prompt_or_messages: Any, temperature: float) -> str:
        """Generate a cache key for the given parameters."""
        return hashlib.md5(
            f"{model}:{str(prompt_or_messages)}:{temperature}".encode('utf-8')
        ).hexdigest()
    
    def _get_from_cache(self, key: str) -> Optional[str]:
        """Retrieve response from cache if available."""
        import json
        import os
        
        if not os.path.exists(self.cache_file):
            return None
        
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                cache = json.load(f)
                return cache.get(key)
        except Exception:
            return None
    
    def _save_to_cache(self, key: str, response: str) -> None:
        """Save response to cache."""
        import json
        import os
        
        cache = {}
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    cache = json.load(f)
            except Exception:
                pass
        
        cache[key] = response
        
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def _calculate_dynamic_ctx(self) -> int:
        """Calculate appropriate context window based on workspace size."""
        import os
        
        total_chars = 0
        workspace = settings.workspace
        
        if os.path.exists(workspace):
            for root, dirs, files in os.walk(workspace):
                # Skip unnecessary directories
                if any(skip in root for skip in [".git", "node_modules", "__pycache__"]):
                    continue
                for f in files:
                    try:
                        total_chars += os.path.getsize(os.path.join(root, f))
                    except Exception:
                        pass
        
        est_tokens = (total_chars // 4) + 4000
        
        if est_tokens <= 8192:
            return 8192
        elif est_tokens <= 16384:
            return 16384
        else:
            return min(32768, ((est_tokens + 4095) // 4096) * 4096)
    
    def generate(
        self,
        model: str,
        prompt: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        is_json: bool = False,
        temperature: Optional[float] = None,
        stream_callback: Optional[Callable[[str], None]] = None,
        **kwargs: Any
    ) -> str:
        """Generate text with smart routing and automatic fallback.
        
        Args:
            model: Preferred model identifier.
            prompt: Simple prompt string.
            messages: Chat messages list.
            is_json: Request JSON output.
            temperature: Override default temperature.
            stream_callback: Optional streaming callback.
            
        Returns:
            Generated text response.
        """
        # Apply smart routing if enabled
        if settings.smart_routing:
            content_to_check = prompt or ""
            if not content_to_check and messages:
                content_to_check = "\n".join(m.get("content", "") for m in messages)
            content_to_check = content_to_check.lower()
            
            # Detect planning/review tasks
            is_planning = any(x in content_to_check for x in [
                "arquitecto", "architect", "plan técnico", "planificación",
                "review", "analizando calidad", "revisa los archivos", "spec.md"
            ])
            
            if is_planning:
                # Use more capable models for planning
                if model.startswith("gemini-"):
                    model = "gemini-2.5-pro"
                elif model.startswith(("gpt-", "o1-", "o3-")):
                    model = "gpt-4o"
            else:
                # Use faster/cheaper models for generation
                if model.startswith("gemini-"):
                    model = "gemini-2.5-flash"
                elif model.startswith(("gpt-", "o1-", "o3-")):
                    model = "gpt-4o-mini"
        
        # Adjust temperature based on linter retries
        if temperature is None:
            temperature = max(0.0, settings.temperature - (state.linter_retries * 0.15))
        
        # Add system prompt if configured
        system_prompt = settings.system_prompt
        if system_prompt and (not system_prompt.startswith("Eres el Orquestador") or is_json):
            if messages:
                has_system = any(m.get("role") == "system" for m in messages)
                if not has_system:
                    messages = [{"role": "system", "content": system_prompt}] + messages
            else:
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]
                prompt = None
        
        # Estimate tokens for tracking
        prompt_tokens = 0
        if prompt:
            prompt_tokens = len(prompt) // 4
        elif messages:
            prompt_tokens = sum(len(m.get('content', '')) for m in messages) // 4
        
        # Check cache first
        cache_key = self._get_cache_key(model, prompt or messages, temperature)
        cached_response = self._get_from_cache(cache_key)
        if cached_response is not None:
            state.cache_hits += 1
            state.token_in += prompt_tokens
            response_tokens = len(cached_response) // 4
            state.token_out += response_tokens
            
            agent_name = kwargs.get("agent_name")
            if agent_name:
                agent_key = agent_name.lower().strip()
                if not hasattr(state, "graph_node_tokens"):
                    state.graph_node_tokens = {}
                state.graph_node_tokens[agent_key] = state.graph_node_tokens.get(agent_key, 0) + prompt_tokens + response_tokens
            
            print("⚡ [LLM CACHE HIT] Retornando respuesta guardada de caché local.")
            return cached_response
        
        state.token_in += prompt_tokens
        num_ctx = self._calculate_dynamic_ctx()
        
        # Determine which provider to use and execute with fallback chain
        response = self._generate_with_fallback(
            model=model,
            prompt=prompt,
            messages=messages,
            is_json=is_json,
            temperature=temperature,
            num_ctx=num_ctx,
            stream_callback=stream_callback
        )
        
        # Track response tokens and cost
        response_tokens = len(response) // 4
        state.token_out += response_tokens
        
        agent_name = kwargs.get("agent_name")
        if agent_name:
            agent_key = agent_name.lower().strip()
            if not hasattr(state, "graph_node_tokens"):
                state.graph_node_tokens = {}
            state.graph_node_tokens[agent_key] = state.graph_node_tokens.get(agent_key, 0) + prompt_tokens + response_tokens
        
        # Update cost tracking (simplified estimation)
        if model.startswith("gemini-"):
            input_cost = (prompt_tokens / 1_000_000) * 0.075
            output_cost = (response_tokens / 1_000_000) * 0.30
            state.cost_usd += input_cost + output_cost
        elif model.startswith(("gpt-", "o1-", "o3-")):
            input_cost = (prompt_tokens / 1_000_000) * 2.50
            output_cost = (response_tokens / 1_000_000) * 10.00
            state.cost_usd += input_cost + output_cost
        
        # Cache the response
        self._save_to_cache(cache_key, response)
        
        return response
    
    def _generate_with_fallback(
        self,
        model: str,
        prompt: Optional[str],
        messages: Optional[List[Dict[str, str]]],
        is_json: bool,
        temperature: float,
        num_ctx: int,
        stream_callback: Optional[Callable[[str], None]]
    ) -> str:
        """Execute generation with automatic fallback between providers."""
        is_gemini = model.startswith("gemini-")
        is_openai = model.startswith(("gpt-", "o1-", "o3-"))
        is_openrouter = model.startswith("openrouter/")
        
        # Try primary provider first
        try:
            if is_gemini and self.gemini.is_available():
                return self.gemini.generate(
                    model, prompt, messages, is_json, temperature
                )
            elif is_openai and self.openai.is_available():
                return self.openai.generate(
                    model, prompt, messages, is_json, temperature
                )
            elif is_openrouter and self.openrouter.is_available():
                real_model = model.replace("openrouter/", "", 1)
                return self.openrouter.generate(
                    real_model, prompt, messages, is_json, temperature
                )
            elif self.ollama.is_available():
                # Local Ollama model
                return self.ollama.generate(
                    model, prompt, messages, is_json, temperature,
                    num_ctx=num_ctx, stream_callback=stream_callback
                )
            else:
                raise Exception("No LLM provider available")
                
        except Exception as e:
            # Fallback logic
            print(f"⚠️ Primary provider failed: {e}")
            
            # Try Ollama as universal fallback
            if self.ollama.is_available():
                ollama_models = self.ollama.list_models()
                if ollama_models:
                    fallback_model = get_fallback_model(ollama_models)
                    state.log(f"⚠️ [FALLBACK] Usando modelo local de Ollama: {fallback_model}")
                    return self.ollama.generate(
                        fallback_model, prompt, messages, is_json, temperature,
                        num_ctx=num_ctx
                    )
            
            # Try Gemini as secondary fallback
            if self.gemini.is_available() and not is_gemini:
                state.log("⚠️ [FALLBACK] Derivando llamada a gemini-2.5-flash...")
                return self.gemini.generate(
                    "gemini-2.5-flash", prompt, messages, is_json, temperature
                )
            
            # Re-raise if no fallback worked
            raise
