import pytest
import os
import shutil
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from squad_local_refactored.src.core.config import settings
from squad_local_refactored.src.core.state import state
from squad_local_refactored.src.pipeline.graph_orchestrator import (
    is_graph_mode_available,
    run_graph_pipeline,
    resume_graph_pipeline,
    resume_after_spec_approval,
    route_after_review,
    route_after_qa,
    SquadGraphState,
    _build_graph
)
from squad_local_refactored.src.api.server import create_app
from squad_local_refactored.src.tools.sys_tools import SysTools

def test_settings_default_orchestrator_mode():
    assert settings.orchestrator_mode == "legacy"
    assert settings.graph_max_retries == 3
    assert settings.graph_checkpoint_db == "squad_checkpoints.sqlite"

def test_is_graph_mode_available():
    res = is_graph_mode_available()
    assert isinstance(res, bool)

def test_run_graph_pipeline_not_available(monkeypatch):
    monkeypatch.setattr("squad_local_refactored.src.pipeline.graph_orchestrator.LANGGRAPH_AVAILABLE", False)
    with pytest.raises(RuntimeError) as excinfo:
        run_graph_pipeline("Test goal", "gemini-2.5-flash")
    assert "LangGraph no está instalado" in str(excinfo.value)

def test_route_after_review():
    state_mock = {
        "review_verdict": "FAIL",
        "retries": {"backend": 1},
        "messages": []
    }
    # settings.graph_max_retries is 3
    assert route_after_review(state_mock) == "fix_backend"

    state_mock_max = {
        "review_verdict": "FAIL",
        "retries": {"backend": 3},
        "messages": []
    }
    assert route_after_review(state_mock_max) == "qa"
    assert "Máximo de reintentos de Backend agotado" in state_mock_max["messages"][-1]

    state_mock_pass = {
        "review_verdict": "PASS",
        "retries": {"backend": 1},
        "messages": []
    }
    assert route_after_review(state_mock_pass) == "qa"

def test_route_after_qa():
    state_mock_ok = {
        "last_errors": [],
        "retries": {"fix": 0}
    }
    assert route_after_qa(state_mock_ok) == "devops"

    state_mock_err = {
        "last_errors": ["Some error"],
        "retries": {"fix": 1}
    }
    assert route_after_qa(state_mock_err) == "fix_qa"

    state_mock_max = {
        "last_errors": ["Some error"],
        "retries": {"fix": 3}
    }
    assert route_after_qa(state_mock_max) == "devops"

def test_resume_nonexistent_run():
    assert resume_graph_pipeline("nonexistent-run-id-12345") is False
    assert resume_after_spec_approval("nonexistent-run-id-12345") is False

def test_graph_status_endpoint():
    app = create_app()
    client = TestClient(app)
    
    state.graph_run_id = "test-run-123"
    state.graph_node_status = {"architect": "done", "dba": "executing"}
    state.graph_last_error = "Mock Review Error"
    state.pipeline_status = "waiting_spec_approval"
    
    response = client.get("/api/graph/status")
    assert response.status_code == 200
    data = response.json()
    assert data["run_id"] == "test-run-123"
    assert data["current_node"] == "dba" # 'dba' is executing
    assert data["node_status"]["dba"] == "executing"
    assert data["last_error"] == "Mock Review Error"
    assert data["is_paused_hitl"] is True

def test_graph_execution_hitl_and_retry_limits(monkeypatch, tmp_path):
    # Setup test workspace
    original_workspace = SysTools.WORKSPACE
    SysTools.WORKSPACE = str(tmp_path)
    
    # Mock AIProvider to simulate architect and then failures
    call_count = 0
    def mock_generate(self, model, prompt, is_json=False):
        nonlocal call_count
        call_count += 1
        if "architect" in prompt or "Diseñando" in prompt or "ARQUITECTO" in prompt:
            return "STACK: FASTAPI_HTMX\nAllowed files: main_output.py"
        elif "dba" in prompt or "DBA" in prompt:
            return "@@FILE: schema.sql\nCREATE TABLE test (id INTEGER);"
        elif "frontend" in prompt or "UI" in prompt:
            return "@@FILE: index.html\n<html></html>"
        elif "backend" in prompt or "BACKEND" in prompt:
            return "@@FILE: main_output.py\nprint('Hello')"
        elif "review" in prompt or "REVIEWER" in prompt:
            return "SÍ_CRITICO: Failed review review"
        elif "fix" in prompt or "LINTER" in prompt:
            return "@@FILE: main_output.py\nprint('Hello')"
        return "Generic response"
        
    monkeypatch.setattr("squad_local_refactored.src.llm.provider.AIProvider.generate", mock_generate)
    
    # Setup environment variables for test
    monkeypatch.setenv("GEMINI_API_KEY", "mock-key")
    
    try:
        # Run graph pipeline - will halt after architect (due to interrupt_after)
        run_id = run_graph_pipeline("Test project", "gemini-2.5-flash")
        assert run_id is not None
        assert state.pipeline_status == "waiting_spec_approval"
        
        # Resume pipeline (DBA, Frontend, Backend, Review)
        # Review always returns SÍ_CRITICO, so it goes backend -> review -> fix -> backend -> review -> ...
        # Since settings.graph_max_retries is 3, it should terminate without infinite looping
        settings.graph_max_retries = 2
        success = resume_graph_pipeline(run_id)
        assert success is True
        
        # Verify it terminated (pipeline_status becomes idle, not waiting_spec_approval)
        assert state.pipeline_status == "idle"
        
    finally:
        SysTools.WORKSPACE = original_workspace
