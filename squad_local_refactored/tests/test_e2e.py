"""E2E Integration Test for SQUAD modular backend.

Tests the full orchestration pipeline with mock LLM generation.
"""

import os
import shutil
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Set env vars for testing before importing modules
os.environ["GEMINI_API_KEY"] = "mock_gemini_key"
os.environ["OPENAI_API_KEY"] = "mock_openai_key"

from src.api.server import create_app
from src.core.state import state
from src.tools.sys_tools import SysTools


# Mock responses for different agent prompts based on keywords in prompts.py
def mock_generate_fn(self, model, prompt=None, messages=None, is_json=False, temperature=0.3, **kwargs):
    prompt_str = prompt or ""
    if not prompt_str and messages:
        prompt_str = "\n".join(m.get("content", "") for m in messages)

    print(f"\n--- DEBUG PROMPT (Model: {model}) ---")
    print(prompt_str[:150])
    
    if "Arquitecto Senior" in prompt_str or "preflight" in prompt_str:
        print("Selected: ARCHITECT")
        return "# SPEC.md\nThis is a mock spec for a task application.\nDefine: SQLite database, Frontend UI, and FastAPI Backend."
    elif "REGLAS ESTRICTAS DE PORTABILIDAD" in prompt_str or "SECURITY_REPORT.md" in prompt_str:
        print("Selected: DBA")
        return "@@FILE: schema.sql\nCREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT);\n@@ENDFILE@@\n@@FILE: SECURITY_REPORT.md\nAll good.\n@@ENDFILE@@"
    elif "Frontend / UI" in prompt_str or "espectacular" in prompt_str or "Tailwind Play" in prompt_str:
        print("Selected: FRONTEND")
        return "@@FILE: index.html\n<html><body><h1>Mock App</h1></body></html>\n@@ENDFILE@@\n@@FILE: styles.css\nbody { background: #000; }\n@@ENDFILE@@"
    elif "Backend/Archivos" in prompt_str or "PUERTO DINÁMICO" in prompt_str:
        print("Selected: BACKEND")
        return "@@FILE: app.py\nfrom fastapi import FastAPI\napp = FastAPI()\n@app.get('/')\ndef read_root(): return {'hello': 'world'}\n@@ENDFILE@@\n@@FILE: requirements.txt\nfastapi\nuvicorn\n@@ENDFILE@@\n@@FILE: main_output.py\nimport uvicorn\nif __name__ == '__main__': uvicorn.run('app:app')\n@@ENDFILE@@"
    elif "Code Reviewer" in prompt_str or "calidad de código" in prompt_str:
        print("Selected: CODE REVIEWER")
        return "El código está limpio. No se detectaron fallos críticos. EXCELENTE"
    elif "Auditor UX" in prompt_str or "VISUAL_REPORT.md" in prompt_str:
        print("Selected: UX AUDITOR")
        return "Auditoría visual completada. Todo luce premium."
    elif "QA & DEVOPS" in prompt_str or "Testing y Pipeline" in prompt_str:
        print("Selected: DEVOPS QA")
        return "@@FILE: .github/workflows/ci.yml\nname: CI\non: push\n@@ENDFILE@@"
    print("Selected: DEFAULT")
    return "Mocked AI Response"


@pytest.fixture
def client():
    app = create_app()
    # Configure workspace to a temporary folder during tests
    test_workspace = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_workspace"))
    os.makedirs(test_workspace, exist_ok=True)
    SysTools.WORKSPACE = test_workspace
    state.pending_writes = {}
    state.logs = []
    state.launcher_logs = []
    state.is_running = False
    state.pipeline_status = "idle"
    state.interception_enabled = False  # Disable interception so critical files write directly

    # Initialize a dummy git repo inside the test workspace to avoid git errors
    subprocess_args = {"cwd": test_workspace, "capture_output": True, "shell": True}
    import subprocess
    subprocess.run("git init", **subprocess_args)
    subprocess.run("git config user.name 'Test User'", **subprocess_args)
    subprocess.run("git config user.email 'test@example.com'", **subprocess_args)

    yield TestClient(app)

    # Cleanup workspace after test
    shutil.rmtree(test_workspace, ignore_errors=True)


@patch("src.llm.provider.AIProvider.generate", new=mock_generate_fn)
@patch("src.tools.sys_tools.SysTools.web_search", return_value="Mock best practices search context")
def test_full_pipeline_e2e(mock_search, client):
    # 1. Clear workspace
    response = client.post("/api/fs/clear-workspace")
    assert response.status_code == 200
    assert response.json()["success"] is True

    # 2. Run agent pipeline Phase 1
    response = client.post("/api/run-agent", json={"goal": "Crear una app de tareas", "model": "gemini-2.5-flash"})
    assert response.status_code == 200
    assert response.json() == "OK"

    # Verify Phase 1 completion (since background tasks in TestClient run synchronously)
    assert os.path.exists(os.path.join(SysTools.WORKSPACE, "SPEC.md"))
    assert state.pipeline_status == "waiting_spec_approval"

    # 3. Approve SPEC.md to run Phase 2
    response = client.post("/api/spec/approve")
    assert response.status_code == 200
    assert response.json()["success"] is True

    # Verify Phase 2 completion and file generation
    assert state.pipeline_status == "idle"
    assert os.path.exists(os.path.join(SysTools.WORKSPACE, "schema.sql"))
    assert os.path.exists(os.path.join(SysTools.WORKSPACE, "index.html"))
    assert os.path.exists(os.path.join(SysTools.WORKSPACE, "styles.css"))
    assert os.path.exists(os.path.join(SysTools.WORKSPACE, "app.py"))
    assert os.path.exists(os.path.join(SysTools.WORKSPACE, "requirements.txt"))
    assert os.path.exists(os.path.join(SysTools.WORKSPACE, "main_output.py"))
