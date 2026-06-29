from .repl_session import BaseREPLSession
import subprocess
import os
import json
import atexit
import threading
import queue


class NodeREPLSession(BaseREPLSession):
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

        worker_path = os.path.join(os.path.dirname(__file__), "node_worker.js")

        try:
            self.process = subprocess.Popen(
                ["node", worker_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.workspace
            )
        except FileNotFoundError:
            # Fallback placeholder if Node is missing on the host
            self.process = None
            return

        # Start background reader thread
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
        if self.process is None:
            return {
                "success": False,
                "output": "",
                "error": "Node.js no está instalado o no se encuentra en el PATH. Consola Node desactivada."
            }

        if self.process.poll() is not None:
            self._start_worker()

        payload = json.dumps({"code": code_str}) + "\n"
        try:
            self.process.stdin.write(payload)
            self.process.stdin.flush()
        except Exception as e:
            self._start_worker()
            return {
                "success": False,
                "output": "",
                "error": f"Failed to communicate with Node REPL worker: {e}"
            }

        try:
            line = self.stdout_queue.get(timeout=5.0)
            result = json.loads(line)

            if len(result.get("output", "")) > 10000:
                result["output"] = result["output"][:10000] + "\n[OUTPUT TRUNCATED - MAX 10KB REACHED]"
            if len(result.get("error", "")) > 10000:
                result["error"] = result["error"][:10000] + "\n[ERROR TRUNCATED]"

            return result
        except queue.Empty:
            self.close()
            self._start_worker()
            return {
                "success": False,
                "output": "",
                "error": "Timeout de ejecución de 5 segundos excedido en Node REPL. El proceso fue terminado."
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
