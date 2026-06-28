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
    SquadGraphState
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

def test_review_loop_goes_directly_to_backend(monkeypatch):
    """Tras review FAIL, el grafo vuelve a backend (no a un nodo fix fantasma)."""
    state_v = {"review_verdict": "FAIL", "retries": {"backend": 0}, "last_errors": ["err"], "messages": []}
    assert route_after_review(state_v) == "fix_backend"

def test_review_loop_terminates_at_max_retries(monkeypatch):
    """El bucle review->backend->review termina en max_retries+1 iteraciones."""
    state_v = {"review_verdict": "FAIL", "retries": {"backend": 0}, "last_errors": ["err"], "messages": []}
    steps = 0
    backend_runs = 0
    while steps < 20:
        r = route_after_review(state_v)
        if r == "fix_backend":
            state_v["retries"]["backend"] += 1
            backend_runs += 1
        elif r == "qa":
            break
        steps += 1
    assert backend_runs <= 3  # graph_max_retries
    assert steps < 20          # no loop infinito

def test_qa_loop_goes_to_fix():
    state_v = {"last_errors": ["test failed"], "retries": {"fix": 0}, "messages": []}
    assert route_after_qa(state_v) == "fix_qa"   # QA sí va a fix

def test_resume_with_invalid_run_id_returns_false(monkeypatch, tmp_path):
    """run_id inexistente retorna False sin abrir el saver."""
    from squad_local_refactored.src.pipeline import graph_orchestrator as go
    monkeypatch.setattr(go.SysTools, "WORKSPACE", str(tmp_path))
    # No crear el archivo sqlite, simular que no existe
    result = go.resume_graph_pipeline("nonexistent_run_123")
    assert result is False

def test_fix_node_paused_on_destructive_cmd(monkeypatch, tmp_path):
    """Si el fix genera un execute_cmd destructivo, el grafo pausa para HITL."""
    from squad_local_refactored.src.pipeline import graph_orchestrator as go
    from squad_local_refactored.src.core.state import state as global_state
    
    monkeypatch.setattr(go.SysTools, "WORKSPACE", str(tmp_path))
    # Mock del LLM: devuelve un execute_cmd con rm -rf
    import json
    malicious_cmd = json.dumps([{"tool": "execute_cmd", "parameters": {"cmd": "rm -rf /tmp/x"}}])
    monkeypatch.setattr(go.AIProvider, "generate", lambda self, **kw: malicious_cmd)
    
    state_val = {
        "prompt": "test", "model": "gemini", "target_model": "gemini",
        "search_ctx": "", "plan": "", "stack": "FASTAPI_HTMX",
        "created_files": [], "last_errors": ["some error"],
        "review_verdict": "FAIL", "retries": {"fix": 0}, "messages": []
    }
    # Clear status
    global_state.pipeline_status = "running"
    
    result = go.node_fix(state_val)
    assert global_state.pipeline_status == "waiting_hitl_approval"
    assert result["messages"][-1].startswith("HITL paused")

def test_fix_node_runs_benign_cmd(monkeypatch, tmp_path):
    """Un execute_cmd benigno se ejecuta sin pausa."""
    from squad_local_refactored.src.pipeline import graph_orchestrator as go
    from squad_local_refactored.src.core.state import state as global_state
    
    monkeypatch.setattr(go.SysTools, "WORKSPACE", str(tmp_path))
    import json
    benign_cmd = json.dumps([{"tool": "execute_cmd", "parameters": {"cmd": "echo hello"}}])
    monkeypatch.setattr(go.AIProvider, "generate", lambda self, **kw: benign_cmd)
    # Limpiar estado
    global_state.pipeline_status = "running"
    
    state_val = {
        "prompt": "test", "model": "gemini", "target_model": "gemini",
        "search_ctx": "", "plan": "", "stack": "FASTAPI_HTMX",
        "created_files": [], "last_errors": ["some error"],
        "destructive_calls": [], "retries": {"fix": 0}, "messages": []
    }
    go.node_fix(state_val)
    assert global_state.pipeline_status != "waiting_hitl_approval"  # no pausó

def test_fix_node_paused_on_destructive_cmd_real_checkpoint(monkeypatch, tmp_path):
    """Prueba que en la compilación y ejecución real, tras node_fix con comando destructivo,
    el checkpoint del grafo queda pausado con next=['qa']."""
    from squad_local_refactored.src.pipeline import graph_orchestrator as go
    from squad_local_refactored.src.core.state import state as global_state
    
    monkeypatch.setattr(go.SysTools, "WORKSPACE", str(tmp_path))
    monkeypatch.setenv("GEMINI_API_KEY", "mock-key")
    
    # Mock de generación de LLM para cada fase
    import json
    malicious_cmd = json.dumps([{"tool": "execute_cmd", "parameters": {"cmd": "rm -rf /tmp/x"}}])
    
    def mock_generate(self, model, prompt, is_json=False):
        with open("prompt_debug.txt", "w", encoding="utf-8") as f:
            f.write(prompt)
        p_lower = prompt.lower()
        if "revisa los archivos creados" in p_lower:
            return "SÍ_CRITICO: Failed review review"
        elif "arquitecto" in p_lower:
            return "STACK: FASTAPI_HTMX\nAllowed files: main_output.py"
        elif "esquema sql" in p_lower:
            return "@@FILE: schema.sql\nCREATE TABLE test (id INTEGER);"
        elif "diseñador" in p_lower:
            return "@@FILE: index.html\n<html></html>"
        elif "escribe el backend" in p_lower or "servidor express" in p_lower or "auto-generada por streamlit" in p_lower:
            return "@@FILE: main_output.py\nprint('Hello')"
        elif "escribe scripts de test" in p_lower:
            import json
            return json.dumps([{
                "tool": "write_file",
                "parameters": {
                    "path": "test_fail_test.py",
                    "content": "def test_always_fails():\n    assert False\n"
                }
            }])
        elif "corrige estos errores" in p_lower or "linter" in p_lower or "corregir" in p_lower:
            # Devuelve comando destructivo
            return malicious_cmd
        return "Generic"
        
    monkeypatch.setattr("squad_local_refactored.src.llm.provider.AIProvider.generate", mock_generate)
    
    # Ejecutamos el pipeline (se pausará en architect)
    run_id = go.run_graph_pipeline("Test project", "gemini-2.5-flash")
    assert global_state.pipeline_status == "waiting_spec_approval"
    
    # Reanudamos. Debería avanzar por DBA, Frontend, Backend, Review (que falla), y entrar en Fix.
    # En Fix, generará el comando destructivo, por lo que el grafo se pausará de verdad.
    success = go.resume_graph_pipeline(run_id)
    assert success is True
    assert global_state.pipeline_status == "waiting_hitl_approval"
    
    # Verificamos que el checkpoint next es de verdad 'qa'
    config = {"configurable": {"thread_id": run_id}}
    def _check_next(app):
        state_info = app.get_state(config)
        assert state_info.next == ("qa",)
    go._run_with_saver(_check_next)


