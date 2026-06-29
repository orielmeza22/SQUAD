from abc import ABC, abstractmethod
import subprocess
import os
import sys
import json
import atexit
import threading
import queue


class BaseREPLSession(ABC):
    @abstractmethod
    def run_code(self, code_str: str) -> dict:
        pass

    @abstractmethod
    def close(self):
        pass


class PythonREPLSession(BaseREPLSession):
    def __init__(self, workspace: str):
        self.workspace = workspace
        self.process = None
        self.stdout_queue = queue.Queue()
        self.reader_thread = None
        self._start_worker()
        atexit.register(self.close)

    def _start_worker(self):
        if self.process and self.process.poll() is None:
            try:
                self.process.kill()
            except Exception:
                pass

        worker_path = os.path.join(os.path.dirname(__file__), "repl_worker.py")
        env = os.environ.copy()
        env["PYTHONPATH"] = os.path.abspath(self.workspace)

        self.process = subprocess.Popen(
            [sys.executable, worker_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            cwd=self.workspace
        )

        # Clear stdout queue and start background reader thread
        self.stdout_queue = queue.Queue()
        self.reader_thread = threading.Thread(target=self._read_stdout, daemon=True)
        self.reader_thread.start()

    def _read_stdout(self):
        while self.process and self.process.poll() is None:
            try:
                line = self.process.stdout.readline()
                if not line:
                    break
                self.stdout_queue.put(line)
            except Exception:
                break

    def run_code(self, code_str: str) -> dict:
        if not self.process or self.process.poll() is not None:
            self._start_worker()

        # Auto path injection to import modules from workspace
        bootstrap_code = f"import sys; sys.path.insert(0, {repr(os.path.abspath(self.workspace))})\n"
        
        payload = json.dumps({"code": bootstrap_code + code_str}) + "\n"
        try:
            self.process.stdin.write(payload)
            self.process.stdin.flush()
        except Exception as e:
            self._start_worker()
            return {
                "success": False,
                "output": "",
                "error": f"Failed to communicate with REPL worker: {e}"
            }

        try:
            # 5-second execution timeout
            line = self.stdout_queue.get(timeout=5.0)
            result = json.loads(line)

            # Truncate large output buffers (max 10KB)
            if len(result.get("output", "")) > 10000:
                result["output"] = result["output"][:10000] + "\n[OUTPUT TRUNCATED - MAX 10KB REACHED]"
            if len(result.get("error", "")) > 10000:
                result["error"] = result["error"][:10000] + "\n[ERROR TRUNCATED]"

            return result
        except queue.Empty:
            # Kill and restart hung worker process
            self.close()
            self._start_worker()
            return {
                "success": False,
                "output": "",
                "error": "Timeout de ejecución de 5 segundos excedido. El proceso fue terminado para evitar bloqueos."
            }

    def close(self):
        if self.process:
            try:
                self.process.stdin.close()
            except Exception:
                pass
            try:
                self.process.kill()
            except Exception:
                pass
            self.process = None
