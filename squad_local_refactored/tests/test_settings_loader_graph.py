import os
import json
import pytest
from squad_local_refactored.src.core.config import settings as pydantic_settings
from squad_local_refactored.src.core import settings_loader

def test_settings_loader_graph_defaults(monkeypatch, tmp_path):
    # Ensure SETTINGS_FILE points to a nonexistent file in tmp_path
    temp_json = tmp_path / "squad_settings.json"
    monkeypatch.setattr(settings_loader, "SETTINGS_FILE", str(temp_json))
    
    # 1. Default loading when no squad_settings.json exists
    data = settings_loader.load_settings()
    assert data["orchestrator_mode"] == "legacy"
    assert data["graph_max_retries"] == 3
    assert data["graph_checkpoint_db"] == "squad_checkpoints.sqlite"
    
    assert pydantic_settings.orchestrator_mode == "legacy"
    assert pydantic_settings.graph_max_retries == 3
    assert pydantic_settings.graph_checkpoint_db == "squad_checkpoints.sqlite"
    assert pydantic_settings.rag_enabled is False
    assert pydantic_settings.rag_collection_name == "squad_workspace"

def test_settings_loader_graph_load_from_json(monkeypatch, tmp_path):
    temp_json = tmp_path / "squad_settings.json"
    monkeypatch.setattr(settings_loader, "SETTINGS_FILE", str(temp_json))
    
    # Write custom settings
    custom = {
        "workspace": str(tmp_path / "SQUAD_WORKSPACE"),
        "ollama_host": "http://localhost:11434",
        "default_model": "gemini-2.5-flash",
        "temperature": 0.5,
        "enable_rag": False,
        "orchestrator_mode": "graph",
        "graph_max_retries": 5,
        "graph_checkpoint_db": "custom_checkpoints.sqlite",
        "rag_enabled": True,
        "rag_collection_name": "custom_collection"
    }
    with open(temp_json, "w", encoding="utf-8") as f:
        json.dump(custom, f)
        
    data = settings_loader.load_settings()
    assert data["orchestrator_mode"] == "graph"
    assert data["graph_max_retries"] == 5
    assert data["graph_checkpoint_db"] == "custom_checkpoints.sqlite"
    assert data["rag_enabled"] is True
    assert data["rag_collection_name"] == "custom_collection"
    
    assert pydantic_settings.orchestrator_mode == "graph"
    assert pydantic_settings.graph_max_retries == 5
    assert pydantic_settings.graph_checkpoint_db == "custom_checkpoints.sqlite"
    assert pydantic_settings.rag_enabled is True
    assert pydantic_settings.rag_collection_name == "custom_collection"

def test_settings_loader_graph_save_and_reload(monkeypatch, tmp_path):
    temp_json = tmp_path / "squad_settings.json"
    monkeypatch.setattr(settings_loader, "SETTINGS_FILE", str(temp_json))
    
    # Init with default settings
    settings_loader.load_settings()
    
    # Save new settings
    success, msg = settings_loader.save_settings({
        "orchestrator_mode": "graph",
        "graph_max_retries": 10,
        "graph_checkpoint_db": "saved_checkpoints.sqlite",
        "rag_enabled": True,
        "rag_collection_name": "saved_collection"
    })
    assert success is True
    
    # Verify JSON content
    with open(temp_json, "r", encoding="utf-8") as f:
        saved_data = json.load(f)
    assert saved_data["orchestrator_mode"] == "graph"
    assert saved_data["graph_max_retries"] == 10
    assert saved_data["graph_checkpoint_db"] == "saved_checkpoints.sqlite"
    assert saved_data["rag_enabled"] is True
    assert saved_data["rag_collection_name"] == "saved_collection"
    
    # Verify pydantic settings loaded
    assert pydantic_settings.orchestrator_mode == "graph"
    assert pydantic_settings.graph_max_retries == 10
    assert pydantic_settings.graph_checkpoint_db == "saved_checkpoints.sqlite"
    assert pydantic_settings.rag_enabled is True
    assert pydantic_settings.rag_collection_name == "saved_collection"
