"""Configuration management using Pydantic Settings."""

import os
from typing import Optional, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""
    
    # API Keys
    gemini_api_key: Optional[str] = Field(default=None, description="Google Gemini API Key")
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API Key")
    openrouter_api_key: Optional[str] = Field(default=None, description="OpenRouter API Key")
    
    # Application Configuration
    workspace: str = Field(default="./SQUAD_WORKSPACE", description="Path to the workspace directory")
    ollama_host: str = Field(default="http://127.0.0.1:11434", description="Ollama API host URL")
    default_model: str = Field(default="gemini-2.5-flash", description="Default LLM model to use")
    temperature: float = Field(default=0.1, ge=0.0, le=2.0, description="LLM temperature")
    context_window: int = Field(default=16384, description="Context window size for LLM")
    
    # Server Configuration
    port: int = Field(default=8000, ge=1, le=65535, description="Server port")
    host: str = Field(default="0.0.0.0", description="Server host")
    
    # Sandboxing Configuration
    sandbox_mode: str = Field(default="local", description="Sandbox mode: local or docker")
    docker_image_python: str = Field(default="python:3.11-slim", description="Docker image for Python sandbox")
    docker_image_node: str = Field(default="node:20-slim", description="Docker image for Node sandbox")
    
    # LangGraph Orchestrator Settings
    orchestrator_mode: str = Field(default="legacy", description="legacy | graph")
    graph_max_retries: int = Field(default=3, description="Máximo de reintentos por agente en el grafo")
    graph_checkpoint_db: str = Field(default="squad_checkpoints.sqlite", description="Ruta del DB SQLite para checkpoints")
    
    # Feature Flags
    enable_rag: bool = Field(default=True, description="Enable RAG (Retrieval Augmented Generation)")
    interception_enabled: bool = Field(default=True, description="Enable critical file write interception")
    smart_routing: bool = Field(default=False, description="Enable smart model routing based on task type")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    
    # Design Identity (for UX agents)
    design_identity: Dict[str, str] = Field(
        default_factory=lambda: {
            "colors": "Dark elegant (slate, emerald accents)",
            "fonts": "Inter, System Font",
            "style": "Modern Minimalist",
            "preset": "default"
        },
        description="Design system identity"
    )
    
    # System Prompt
    system_prompt: str = Field(
        default="Eres el Orquestador V5. Responde siempre en JSON.",
        description="Default system prompt for LLM interactions"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


# Global settings instance
settings = Settings()


def load_settings_from_json(json_path: str) -> None:
    """Load additional settings from a JSON file (e.g., squad_settings.json)."""
    import json
    
    if not os.path.exists(json_path):
        return
    
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Update settings that are allowed to be overridden
        allowed_overrides = [
            "workspace", "ollama_host", "default_model", "temperature",
            "context_window", "enable_rag", "interception_enabled",
            "smart_routing", "design_identity", "system_prompt"
        ]
        
        for key, value in data.items():
            if key in allowed_overrides and hasattr(settings, key):
                setattr(settings, key, value)
                
    except Exception as e:
        print(f"⚠️ Error loading settings from {json_path}: {e}")


def save_settings_to_json(json_path: str, new_settings: Dict[str, Any]) -> bool:
    """Save settings to a JSON file."""
    import json
    
    try:
        # Load existing settings
        current = {}
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                current = json.load(f)
        
        # Update with new settings
        current.update(new_settings)
        
        # Save back
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(current, f, ensure_ascii=False, indent=2)
        
        # Reload into global settings
        load_settings_from_json(json_path)
        
        return True
    except Exception as e:
        print(f"❌ Error saving settings: {e}")
        return False
