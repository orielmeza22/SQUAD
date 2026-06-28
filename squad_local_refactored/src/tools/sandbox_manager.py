import os
import socket
import subprocess
from typing import List, Tuple, Optional
from ..core.config import settings
from ..core.state import state
from .sys_tools import SysTools

class SandboxManager:
    def __init__(self, mode: str = "local"):
        self.mode = mode if mode in ("local", "docker") else "local"

    def is_available(self) -> bool:
        if self.mode == "local":
            return True
        try:
            res = subprocess.run(["docker", "ps"], capture_output=True, timeout=5)
            return res.returncode == 0
        except Exception:
            return False

    def find_free_port(self) -> int:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind(('127.0.0.1', 0))
            port = s.getsockname()[1]
            return port
        except Exception:
            import random
            return random.randint(20000, 30000)
        finally:
            s.close()

    def cleanup(self, container_id: str) -> None:
        pass

    def run(self, cmd: List[str], cwd: Optional[str] = None, timeout: int = 300) -> Tuple[int, str, str]:
        # Validate command safety before execution (SQUAD 2.0 Security Bypass Fix)
        from .security import SecurityScanner
        import re
        cmd_str = " ".join(cmd)
        for pattern, reason in SecurityScanner.DANGEROUS_SHELL_PATTERNS:
            if re.search(pattern, cmd_str):
                return -1, "", f"SecurityError: Comando bloqueado: {reason}."

        if self.mode == "local":
            return self._run_local(cmd, cwd, timeout)

        # Docker mode
        if not self.is_available():
            state.launcher_logs.append("⚠️ [SANDBOX] Docker no está disponible. Degradando ejecución a modo local.")
            return self._run_local(cmd, cwd, timeout)

        # Detect runtime image based on command contents
        cmd_str_lower = " ".join(cmd).lower()
        if "node" in cmd_str_lower or "npm" in cmd_str_lower or any(c.endswith(('.js', '.ts', '.jsx', '.tsx')) for c in cmd):
            image = settings.docker_image_node
        else:
            image = settings.docker_image_python

        # Find container port and host port via explicit flag scanning, fallback to default_port
        container_port = getattr(state, "default_port", 5000)
        for i, arg in enumerate(cmd):
            if arg in ("--port", "-p", "-port") and i + 1 < len(cmd):
                val = cmd[i + 1]
                if val.isdigit():
                    container_port = int(val)
                    break

        free_port = self.find_free_port()
        workspace_abs = os.path.abspath(SysTools.WORKSPACE)

        # Build docker run command
        docker_cmd = [
            "docker", "run", "--rm",
            "-v", f"{workspace_abs}:/app",
            "-w", "/app",
            "--memory=512m",
            "--cpus=1.0",
            "-p", f"{free_port}:{container_port}",
            image
        ]
        
        # Map arguments that are absolute workspace paths to be container-relative
        docker_args = []
        for arg in cmd:
            if os.path.isabs(arg) and arg.startswith(workspace_abs):
                rel = os.path.relpath(arg, workspace_abs).replace('\\', '/')
                docker_args.append(rel)
            else:
                docker_args.append(arg)

        docker_cmd.extend(docker_args)

        try:
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                env={**os.environ, "PYTHONIOENCODING": "utf-8"}
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", f"Command timed out after {timeout} seconds inside Docker"
        except Exception as e:
            return -1, "", str(e)

    def _run_local(self, cmd: List[str], cwd: Optional[str] = None, timeout: int = 300) -> Tuple[int, str, str]:
        if cwd is None:
            cwd = SysTools.WORKSPACE
        try:
            result = subprocess.run(
                cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout,
                env={**os.environ, "PYTHONIOENCODING": "utf-8"}
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            return -1, "", str(e)
