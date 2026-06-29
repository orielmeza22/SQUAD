import os
import shutil
import pytest
from squad_local_refactored.src.tools.repl_session import PythonREPLSession
from squad_local_refactored.src.tools.repl_security import REPLSecurityValidator
from squad_local_refactored.src.tools.node_repl_session import NodeREPLSession


@pytest.fixture
def temp_workspace(tmp_path):
    workspace_dir = tmp_path / "repl_workspace"
    workspace_dir.mkdir()
    yield str(workspace_dir)
    # Cleanup workspace
    shutil.rmtree(workspace_dir, ignore_errors=True)


def test_repl_isolated_execution_and_persistence(temp_workspace):
    session = PythonREPLSession(temp_workspace)
    try:
        # Run stateful definitions
        r1 = session.run_code("x = 100\ndef get_val():\n    return x + 50")
        assert r1["success"] is True
        
        # Test variable and function persistence
        r2 = session.run_code("print(get_val())")
        assert r2["success"] is True
        assert r2["output"].strip() == "150"
    finally:
        session.close()


def test_repl_process_suicide_isolation(temp_workspace):
    session = PythonREPLSession(temp_workspace)
    try:
        # Cause subprocess hard exit
        r1 = session.run_code("import os; os._exit(99)")
        assert r1["success"] is False
        assert "terminó abruptamente" in r1["error"]
        
        # Next run should auto-restart worker cleanly
        r2 = session.run_code("x = 42\nprint(x)")
        assert r2["success"] is True
        assert r2["output"].strip() == "42"
    finally:
        session.close()


def test_repl_execution_timeout(temp_workspace):
    session = PythonREPLSession(temp_workspace)
    try:
        # Trigger timeout with infinite loop
        r = session.run_code("import time\nwhile True:\n    time.sleep(0.1)")
        assert r["success"] is False
        assert "Timeout" in r["error"] or "terminó abruptamente" in r["error"]
        
        # Next statement should execute fine on restarted worker
        r2 = session.run_code("print('survived')")
        assert r2["success"] is True
        assert r2["output"].strip() == "survived"
    finally:
        session.close()


def test_repl_security_validator():
    # Valid Python code
    ok_py = "x = 10\nprint(x)"
    ok, msg = REPLSecurityValidator.validate_python(ok_py)
    assert ok is True
    assert msg == ""

    # Dangerous OS System Call
    bad_py1 = "import os\nos.system('rm -rf /')"
    ok, msg = REPLSecurityValidator.validate_python(bad_py1)
    assert ok is False
    assert "Bloqueo" in msg

    # Attribute exit calls
    bad_py2 = "import sys\nsys.exit(0)"
    ok, msg = REPLSecurityValidator.validate_python(bad_py2)
    assert ok is False
    assert "Bloqueo" in msg

    # Builtin dynamic exec/eval calls
    bad_py3 = "eval('1 + 1')"
    ok, msg = REPLSecurityValidator.validate_python(bad_py3)
    assert ok is False
    assert "Bloqueo" in msg or "Uso peligroso" in msg
