"""E2E Integration Test for SQUAD modular backend.

Verifies that the API endpoints are reachable and respond correctly
when LangGraph is available as the sole orchestration engine.
"""

import os
import shutil
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

os.environ["GEMINI_API_KEY"] = "mock_gemini_key"
os.environ["OPENAI_API_KEY"] = "mock_openai_key"

from src.api.server import create_app
from src.core.state import state
from src.tools.sys_tools import SysTools


@pytest.fixture
def client():
    app = create_app()
    test_workspace = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_workspace"))
    os.makedirs(test_workspace, exist_ok=True)
    SysTools.WORKSPACE = test_workspace
    state.pending_writes = {}
    state.logs = []
    state.launcher_logs = []
    state.is_running = False
    state.pipeline_status = "idle"
    state.graph_run_id = None
    state.interception_enabled = False

    import subprocess
    subprocess_args = {"cwd": test_workspace, "capture_output": True, "shell": True}
    subprocess.run("git init", **subprocess_args)
    subprocess.run("git config user.name 'Test User'", **subprocess_args)
    subprocess.run("git config user.email 'test@example.com'", **subprocess_args)

    yield TestClient(app)

    shutil.rmtree(test_workspace, ignore_errors=True)


@patch("src.api.routes.agent.run_graph_pipeline")
@patch("src.api.routes.agent.is_graph_mode_available", return_value=True)
def test_full_pipeline_e2e(mock_available, mock_run_graph, client):
    """Verifica que el endpoint /api/run-agent acepta la solicitud y delega al motor LangGraph."""
    # 1. Clear workspace
    response = client.post("/api/fs/clear-workspace")
    assert response.status_code == 200
    assert response.json()["success"] is True

    # 2. Run agent pipeline Phase 1 — debe delegar a run_graph_pipeline
    response = client.post("/api/run-agent", json={"goal": "Crear una app de tareas", "model": "gemini-2.5-flash"})
    assert response.status_code == 200
    assert response.json() == "OK"

    # Verificar que se llamó al motor de grafos (no al legacy)
    mock_run_graph.assert_called_once_with("Crear una app de tareas", "gemini-2.5-flash")


def test_infra_destroy_cleanup(client):
    """Verifica que el endpoint /api/infra/destroy limpia las variables de estado transitorias."""
    # 1. Set some mock active state
    state.pending_writes = {"test.py": "content"}
    state.chat_history = [{"role": "user", "content": "hello"}]
    state.logs = ["log entry 1", "log entry 2"]
    state.launcher_logs = ["launcher log 1"]
    state.active_diagnostic = {"error": "test error", "file": "test.py", "line": 10}

    # 2. Call destroy endpoint
    response = client.post("/api/infra/destroy")
    assert response.status_code == 200
    assert response.json()["success"] is True

    # 3. Assert state is cleared
    assert state.pending_writes == {}
    assert state.chat_history == []
    assert state.logs == []
    assert state.launcher_logs == []
    assert state.active_diagnostic is None

