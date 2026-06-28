"""Settings loader — bridges ``squad_settings.json`` ↔ Pydantic ``Settings`` ↔ ``state``.

Migrated from the legacy monolith ``load_settings()`` / ``save_settings()``.
"""

import json
import os
import threading
from typing import Any, Dict, Tuple

from ..core.config import settings as pydantic_settings
from ..core.state import state
from ..tools.sys_tools import SysTools


_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Look for squad_settings.json alongside the legacy backend first, then in this package
_LEGACY_SETTINGS = os.path.join(_BACKEND_ROOT, "..", "squad_local", "squad_settings.json")
_LOCAL_SETTINGS = os.path.join(_BACKEND_ROOT, "squad_settings.json")
SETTINGS_FILE = _LOCAL_SETTINGS if os.path.exists(_LOCAL_SETTINGS) else _LEGACY_SETTINGS


def _defaults() -> Dict[str, Any]:
    """Return the default settings dict used when no JSON file exists."""
    return {
        "workspace": os.path.join(os.path.dirname(SETTINGS_FILE), "SQUAD_WORKSPACE"),
        "ollama_host": "http://127.0.0.1:11434",
        "default_model": "gemini-2.5-flash",
        "temperature": 0.1,
        "enable_rag": True,
        "default_port": 5000,
        "system_prompt": "Eres el Orquestador V5. Responde siempre en JSON.",
        "context_window": 16384,
        "interception_enabled": True,
        "smart_routing": False,
        "sandbox_mode": "local",
        "docker_image_python": "python:3.11-slim",
        "docker_image_node": "node:20-slim",
        "design_identity": {
            "colors": "Dark elegant (slate, emerald accents)",
            "fonts": "Inter, System Font",
            "style": "Modern Minimalist",
            "preset": "default"
        },
        "orchestrator_mode": "legacy",
        "graph_max_retries": 3,
        "graph_checkpoint_db": "squad_checkpoints.sqlite",
    }


def load_settings() -> Dict[str, Any]:
    """Load settings from ``squad_settings.json`` and apply them into ``state`` + ``SysTools``.

    Returns:
        The merged settings dictionary.
    """
    defaults = _defaults()
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                defaults.update(data)
        except Exception as e:
            print(f"Error loading settings: {e}")

    # Apply to global state
    SysTools.WORKSPACE = os.path.abspath(defaults["workspace"])
    state.active_model = defaults["default_model"]
    state.temperature = defaults["temperature"]
    state.enable_rag = defaults["enable_rag"]
    state.default_port = defaults.get("default_port", 5000)
    state.system_prompt = defaults.get("system_prompt", "Eres el Orquestador V5. Responde siempre en JSON.")
    state.context_window = defaults.get("context_window", 16384)
    state.interception_enabled = defaults.get("interception_enabled", True)
    state.smart_routing = defaults.get("smart_routing", False)
    state.design_identity = defaults.get("design_identity", _defaults()["design_identity"])

    # Apply to Pydantic settings (mutable attrs)
    pydantic_settings.workspace = defaults["workspace"]
    pydantic_settings.ollama_host = defaults["ollama_host"]
    pydantic_settings.default_model = defaults["default_model"]
    pydantic_settings.temperature = defaults["temperature"]
    pydantic_settings.context_window = defaults.get("context_window", 16384)
    pydantic_settings.enable_rag = defaults["enable_rag"]
    pydantic_settings.interception_enabled = defaults.get("interception_enabled", True)
    pydantic_settings.smart_routing = defaults.get("smart_routing", False)
    pydantic_settings.sandbox_mode = defaults.get("sandbox_mode", "local")
    pydantic_settings.docker_image_python = defaults.get("docker_image_python", "python:3.11-slim")
    pydantic_settings.docker_image_node = defaults.get("docker_image_node", "node:20-slim")
    pydantic_settings.design_identity = defaults.get("design_identity", _defaults()["design_identity"])
    pydantic_settings.orchestrator_mode = defaults.get("orchestrator_mode", "legacy")
    pydantic_settings.graph_max_retries = defaults.get("graph_max_retries", 3)
    pydantic_settings.graph_checkpoint_db = defaults.get("graph_checkpoint_db", "squad_checkpoints.sqlite")

    return defaults


def save_settings(new_settings: Dict[str, Any]) -> Tuple[bool, str]:
    """Merge new settings, persist to JSON and apply to ``state``.

    Returns:
        Tuple of (success, message).
    """
    current = load_settings()
    current.update(new_settings)
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(current, f, ensure_ascii=False, indent=2)
        # Re-apply
        SysTools.WORKSPACE = os.path.abspath(current["workspace"])
        state.active_model = current["default_model"]
        state.temperature = current["temperature"]
        state.enable_rag = current["enable_rag"]
        state.default_port = current.get("default_port", 5000)
        state.system_prompt = current.get("system_prompt", "Eres el Orquestador V5. Responde siempre en JSON.")
        state.context_window = current.get("context_window", 16384)
        state.interception_enabled = current.get("interception_enabled", True)
        state.smart_routing = current.get("smart_routing", False)
        state.design_identity = current.get("design_identity", _defaults()["design_identity"])
        pydantic_settings.sandbox_mode = current.get("sandbox_mode", "local")
        pydantic_settings.docker_image_python = current.get("docker_image_python", "python:3.11-slim")
        pydantic_settings.docker_image_node = current.get("docker_image_node", "node:20-slim")
        pydantic_settings.orchestrator_mode = current.get("orchestrator_mode", "legacy")
        pydantic_settings.graph_max_retries = current.get("graph_max_retries", 3)
        pydantic_settings.graph_checkpoint_db = current.get("graph_checkpoint_db", "squad_checkpoints.sqlite")
        return True, "Settings saved"
    except Exception as e:
        return False, str(e)
