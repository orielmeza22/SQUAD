"""Settings and status endpoints.

Migrated 1:1 from the legacy monolith: ``api_get_settings``, ``api_post_settings``,
``api_get_logs``, ``api_get_launcher_logs``, ``api_get_models``, ``api_get_chat_history``.
"""

from fastapi import APIRouter, Body, HTTPException

from ...core.state import state
from ...core.settings_loader import load_settings, save_settings
from ...llm.ollama import OllamaProvider

router = APIRouter()


@router.get("/api/settings")
def api_get_settings():
    """Return current settings."""
    return {"success": True, "settings": load_settings()}


@router.post("/api/settings")
def api_post_settings(data: dict = Body(default={})):
    """Save settings and return the merged result."""
    success, msg = save_settings(data)
    if success:
        return {"success": True, "settings": load_settings()}
    raise HTTPException(status_code=500, detail=msg)


@router.get("/api/logs")
def api_get_logs():
    """Return pipeline logs and status."""
    return {"logs": state.logs, "is_running": state.is_running, "pipeline_status": state.pipeline_status}


@router.get("/api/launcher_logs")
def api_get_launcher_logs():
    """Return launcher logs, active process/port/diagnostic."""
    is_active = state.active_process and state.active_process.poll() is None
    return {
        "logs": state.launcher_logs,
        "is_active": is_active,
        "active_port": getattr(state, "active_port", 5000),
        "active_diagnostic": state.active_diagnostic
    }


@router.get("/api/models")
def api_get_models():
    """Aggregate available model identifiers from all providers."""
    ollama = OllamaProvider()
    ollama_models = ollama.list_models()
    openrouter_models = [
        "openrouter/google/gemini-2.5-flash:free",
        "openrouter/meta-llama/llama-3.1-8b-instruct:free",
        "openrouter/qwen/qwen-2.5-72b-instruct:free"
    ]
    gemini_models = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash", "gemini-2.0-flash-exp"]
    openai_models = ["gpt-4o-mini", "gpt-4o", "o1-mini"]
    models = gemini_models + openrouter_models + openai_models + ollama_models
    return {"models": models}


@router.get("/api/chat-history")
def api_get_chat_history():
    """Return chat history."""
    return {"history": state.chat_history}
