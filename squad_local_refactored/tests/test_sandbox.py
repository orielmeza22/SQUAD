import pytest
from unittest.mock import MagicMock, patch
import subprocess
from squad_local_refactored.src.tools.sandbox_manager import SandboxManager
from squad_local_refactored.src.core.state import state

def test_sandbox_local_mode():
    sandbox = SandboxManager(mode="local")
    assert sandbox.mode == "local"
    assert sandbox.is_available() is True
    
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "hello local"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        rc, out, err = sandbox.run(["echo", "hello"])
        assert rc == 0
        assert out == "hello local"
        mock_run.assert_called_once()
        # Verify it wasn't run with docker run
        args, kwargs = mock_run.call_args
        cmd_called = args[0]
        assert "docker" not in cmd_called

def test_sandbox_find_free_port():
    sandbox = SandboxManager()
    port1 = sandbox.find_free_port()
    assert isinstance(port1, int)
    assert port1 > 0

def test_sandbox_docker_fallback_when_unavailable():
    sandbox = SandboxManager(mode="docker")
    assert sandbox.mode == "docker"
    
    # Mock is_available to return False
    with patch.object(SandboxManager, "is_available", return_value=False):
        state.launcher_logs = []
        with patch.object(SandboxManager, "_run_local", return_value=(0, "local_fallback", "")) as mock_local:
            rc, out, err = sandbox.run(["echo", "hello"])
            assert rc == 0
            assert out == "local_fallback"
            mock_local.assert_called_once()
            # Verify warning was added
            assert any("Docker no está disponible" in log for log in state.launcher_logs)

def test_sandbox_docker_command_generation():
    sandbox = SandboxManager(mode="docker")
    
    with patch.object(SandboxManager, "is_available", return_value=True):
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "docker output"
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            rc, out, err = sandbox.run(["python", "main_output.py", "5000"])
            assert rc == 0
            assert out == "docker output"
            
            mock_run.assert_called_once()
            args, kwargs = mock_run.call_args
            cmd_called = args[0]
            
            # Verify docker execution options
            assert cmd_called[0] == "docker"
            assert "run" in cmd_called
            assert "--rm" in cmd_called
            assert "--memory=512m" in cmd_called
            assert "--cpus=1.0" in cmd_called
            # Verify volume mount
            assert any("-v" == arg for arg in cmd_called)
            # Verify port mapping
            assert any("-p" == arg for arg in cmd_called)
            # Verify image is present
            assert any("python:3.11-slim" in arg for arg in cmd_called)
