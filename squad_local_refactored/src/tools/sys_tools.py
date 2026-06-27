"""System tools: workspace management, file I/O, patches, linter, Git operations, and self-healing.

Migrated 1:1 from the legacy monolith ``squad_local/squad_server.py`` (class ``SysTools``).
"""

import os
import re
import sys
import json
import shutil
import socket
import subprocess
import threading
from typing import List, Optional, Tuple, Dict, Any

import psutil

from ..core.config import settings
from ..core.state import state


def sanitize_workspace_path(path: str) -> str:
    """Sandbox a relative path to within the workspace.

    Args:
        path: Relative (or messily-prefixed) path to resolve inside the workspace.

    Returns:
        Absolute path guaranteed to live inside ``SysTools.WORKSPACE``.

    Raises:
        ValueError: If the resolved path escapes the workspace.
    """
    clean_name = path.lstrip("\\/")
    if ":" in clean_name:
        clean_name = clean_name.split(":", 1)[-1].lstrip("\\/")
    clean_name = os.path.normpath(clean_name)
    while clean_name.startswith("..") or clean_name.startswith("/") or clean_name.startswith("\\"):
        clean_name = clean_name.replace("../", "").replace("..\\", "").replace("..", "").lstrip("\\/")
    full_path = os.path.abspath(os.path.join(SysTools.WORKSPACE, clean_name))
    if not full_path.startswith(os.path.abspath(SysTools.WORKSPACE)):
        raise ValueError("Acceso denegado: fuera del workspace")
    return full_path


class SysTools:
    """System utilities for workspace management, file operations, linting and Git.

    Provides:
    - Workspace setup and virtual environment management
    - Automatic dependency detection (Python/Node.js) and self-healing
    - Safe file read/write with critical-file interception
    - Multi-file @@FILE:/@@PATCH: parsing and application
    - Syntax checking and an autonomous linter
    - Shadow Git operations (init/commit/push) with locking
    """

    WORKSPACE = os.path.abspath(settings.workspace)
    git_lock = threading.Lock()
    broken_memory_files: Dict[str, str] = {}


    # ------------------------------------------------------------------ #
    # Workspace & process management
    # ------------------------------------------------------------------ #
    @staticmethod
    def setup():
        """Initialize the workspace directory."""
        if not os.path.exists(SysTools.WORKSPACE):
            os.makedirs(SysTools.WORKSPACE)

    @staticmethod
    def find_node_entry_point() -> str:
        """Locate the Node.js entry point inside the workspace."""
        if not os.path.exists(SysTools.WORKSPACE):
            return "main_output.js"
        workspace_files = os.listdir(SysTools.WORKSPACE)
        main_files = [
            f for f in workspace_files
            if f.startswith("main_output.") and f.endswith(('.js', '.ts', '.jsx', '.tsx'))
        ]
        if main_files:
            return main_files[0]
        commons = [f for f in ["server.js", "app.js", "index.js", "main.js"] if f in workspace_files]
        if commons:
            return commons[0]
        recursive_commons = []
        for root, _, files in os.walk(SysTools.WORKSPACE):
            if "node_modules" in root or ".git" in root or "venv" in root or "__pycache__" in root:
                continue
            for f in files:
                if f in ["server.js", "app.js", "index.js", "main.js"]:
                    rel_path = os.path.relpath(os.path.join(root, f), SysTools.WORKSPACE).replace('\\', '/')
                    recursive_commons.append(rel_path)
        if recursive_commons:
            recursive_commons.sort(key=lambda x: (
                x.count('/'),
                0 if 'app.js' in x else 1 if 'server.js' in x else 2
            ))
            return recursive_commons[0]
        for root, _, files in os.walk(SysTools.WORKSPACE):
            if "node_modules" in root or ".git" in root or "venv" in root or "__pycache__" in root:
                continue
            for f in files:
                if f.endswith(('.js', '.ts')):
                    rel_path = os.path.relpath(os.path.join(root, f), SysTools.WORKSPACE).replace('\\', '/')
                    return rel_path
        return "main_output.js"

    @staticmethod
    def cleanup_workspace_processes():
        """Kill leftover child processes still attached to the workspace directory."""
        if not os.path.exists(SysTools.WORKSPACE):
            return
        ws_abs = os.path.abspath(SysTools.WORKSPACE)
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.pid == os.getpid():
                    continue
                pname = proc.name().lower()
                if not any(x in pname for x in ["python", "node", "npm", "pip", "cmd", "powershell", "bash"]):
                    continue
                try:
                    cwd = os.path.abspath(proc.cwd())
                    if cwd.startswith(ws_abs):
                        print(f"🧹 [SISTEMA] Matando proceso residual en workspace: PID {proc.pid} ({proc.name()})")
                        proc.kill()
                        continue
                except Exception:
                    pass
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

    @staticmethod
    def kill_process_tree(pid: int):
        """Recursively kill a process and all of its children (OS-aware)."""
        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            for child in children:
                try:
                    child.kill()
                except Exception:
                    pass
            parent.kill()
        except Exception:
            try:
                if sys.platform == 'win32':
                    subprocess.run(f"taskkill /F /T /PID {pid}", shell=True, capture_output=True)
                else:
                    os.kill(pid, 9)
            except Exception:
                pass

    @staticmethod
    def get_free_port(start_port: int) -> int:
        """Find the first free TCP port at or above ``start_port``."""
        port = start_port
        while port < 65535:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('127.0.0.1', port))
                    return port
            except OSError:
                port += 1
        return start_port

    # ------------------------------------------------------------------ #
    # Virtual environment & dependency detection
    # ------------------------------------------------------------------ #
    @staticmethod
    def setup_venv(logger_list: Optional[List[str]] = None) -> Tuple[str, str]:
        """Create (if needed) and return a Python virtual env inside the workspace.

        Args:
            logger_list: Optional list to append log messages to.

        Returns:
            Tuple of (python_executable_path, pip_executable_path).
        """
        venv_dir = os.path.join(SysTools.WORKSPACE, "venv")
        if sys.platform == "win32":
            python_exe = os.path.join(venv_dir, "Scripts", "python.exe")
            pip_exe = os.path.join(venv_dir, "Scripts", "pip.exe")
        else:
            python_exe = os.path.join(venv_dir, "bin", "python")
            pip_exe = os.path.join(venv_dir, "bin", "pip")

        if not os.path.exists(python_exe):
            if logger_list is not None:
                logger_list.append("📦 [SISTEMA] Creando entorno virtual (venv) en el workspace...")
            try:
                subprocess.run(
                    [sys.executable, "-m", "venv", venv_dir],
                    check=True, capture_output=True
                )
                if logger_list is not None:
                    logger_list.append("✅ [SISTEMA] Entorno virtual creado con éxito.")
            except Exception as e:
                if logger_list is not None:
                    logger_list.append(
                        f"⚠️ [SISTEMA] No se pudo crear venv: {e}. Se utilizará Python global."
                    )
                return sys.executable, "pip"
        return python_exe, pip_exe

    @staticmethod
    def auto_detect_nodejs_dependencies() -> None:
        """Detect Node.js dependencies from source files and update package.json."""
        pkg_path = os.path.join(SysTools.WORKSPACE, "package.json")
        detected_deps = set()
        node_builtins = {
            "fs", "path", "child_process", "crypto", "os", "http", "https", "url",
            "querystring", "stream", "util", "assert", "events", "zlib", "buffer",
            "dns", "net", "readline", "repl", "tls", "v8", "vm", "worker_threads",
            "process", "timers", "console"
        }

        if os.path.exists(SysTools.WORKSPACE):
            for root, _, files_in_dir in os.walk(SysTools.WORKSPACE):
                if "node_modules" in root or ".git" in root or "venv" in root or "__pycache__" in root:
                    continue
                for f in files_in_dir:
                    if f.endswith(('.js', '.jsx', '.ts', '.tsx')):
                        try:
                            with open(os.path.join(root, f), 'r', encoding='utf-8') as file_obj:
                                content = file_obj.read()
                            req_matches = re.findall(r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)', content)
                            imp_matches = re.findall(
                                r'(?:import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]|'
                                r'import\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)|'
                                r'import\s+[\'"]([^\'"]+)[\'"])',
                                content
                            )
                            all_matches = req_matches
                            for m in imp_matches:
                                if isinstance(m, tuple):
                                    for part in m:
                                        if part:
                                            all_matches.append(part)
                                elif m:
                                    all_matches.append(m)
                            for dep in all_matches:
                                dep = dep.strip()
                                if not dep:
                                    continue
                                if dep.startswith('.') or dep.startswith('/') or dep.startswith('\\'):
                                    continue
                                if dep.startswith('@'):
                                    parts = dep.split('/')
                                    dep_name = f"{parts[0]}/{parts[1]}" if len(parts) >= 2 else dep
                                else:
                                    dep_name = dep.split('/')[0]
                                if dep_name not in node_builtins:
                                    detected_deps.add(dep_name)
                        except Exception:
                            pass

        pkg_data = {}
        if os.path.exists(pkg_path):
            try:
                with open(pkg_path, 'r', encoding='utf-8') as f_pkg:
                    pkg_data = json.load(f_pkg)
            except Exception:
                pass
        if not isinstance(pkg_data, dict):
            pkg_data = {}
        if "name" not in pkg_data:
            pkg_data["name"] = "squad-workspace-project"
        if "type" not in pkg_data:
            pkg_data["type"] = "commonjs"
        changed = False
        if "scripts" not in pkg_data or not isinstance(pkg_data["scripts"], dict):
            pkg_data["scripts"] = {}
            changed = True

        target_f = SysTools.find_node_entry_point()
        correct_start_cmd = f"node {target_f}"
        current_start = pkg_data["scripts"].get("start", "")
        ref_file = None
        if current_start.strip().startswith("node "):
            ref_file = current_start.strip()[5:].strip()
        elif current_start.strip().startswith("nodemon "):
            ref_file = current_start.strip()[8:].strip()
        file_missing = False
        if ref_file:
            ref_file = ref_file.replace('"', '').replace("'", "")
            ref_path = os.path.join(SysTools.WORKSPACE, ref_file)
            if not os.path.exists(ref_path):
                file_missing = True
        is_invalid = (
            not current_start
            or ".bat" in current_start
            or ".sh" in current_start
            or ".py" in current_start
            or ".md" in current_start
            or file_missing
        )
        if is_invalid:
            pkg_data["scripts"]["start"] = correct_start_cmd
            changed = True

        if "dependencies" not in pkg_data or not isinstance(pkg_data["dependencies"], dict):
            pkg_data["dependencies"] = {}
            changed = True
        for dep in detected_deps:
            if dep not in pkg_data["dependencies"]:
                pkg_data["dependencies"][dep] = "*"
                changed = True

        if changed or not os.path.exists(pkg_path):
            try:
                with open(pkg_path, 'w', encoding='utf-8') as f_pkg:
                    json.dump(pkg_data, f_pkg, indent=2)
            except Exception:
                pass

    @staticmethod
    def auto_detect_python_dependencies() -> None:
        """Detect Python dependencies from source files and update requirements.txt."""
        req_path = os.path.join(SysTools.WORKSPACE, "requirements.txt")
        detected_modules = set()
        py_builtins = {
            "os", "sys", "re", "math", "json", "datetime", "time", "random", "hashlib",
            "subprocess", "shutil", "urllib", "collections", "itertools", "functools",
            "typing", "io", "csv", "sqlite3", "threading", "logging", "asyncio", "xml",
            "socket", "select", "selectors", "signal", "tempfile", "traceback", "uuid"
        }

        if os.path.exists(SysTools.WORKSPACE):
            for root, _, files_in_dir in os.walk(SysTools.WORKSPACE):
                if "node_modules" in root or ".git" in root or "venv" in root or "__pycache__" in root:
                    continue
                for f in files_in_dir:
                    if f.endswith('.py'):
                        try:
                            with open(os.path.join(root, f), 'r', encoding='utf-8') as file_obj:
                                content = file_obj.read()
                            for line in content.splitlines():
                                line = line.strip()
                                if line.startswith('import '):
                                    parts = line[7:].split(',')
                                    for p in parts:
                                        p_strip = p.strip()
                                        if not p_strip:
                                            continue
                                        mod = p_strip.split()[0].split('.')[0]
                                        if mod and mod not in py_builtins:
                                            detected_modules.add(mod)
                                elif line.startswith('from '):
                                    parts = line[5:].strip().split()
                                    if parts:
                                        mod = parts[0].split('.')[0]
                                        if mod and mod not in py_builtins:
                                            detected_modules.add(mod)
                        except Exception:
                            pass

        if detected_modules:
            package_mapping = {
                "flask": "flask",
                "sqlalchemy": "SQLAlchemy",
                "sqlmodel": "sqlmodel",
                "fastapi": "fastapi",
                "uvicorn": "uvicorn",
                "jinja2": "Jinja2",
                "requests": "requests",
                "pydantic": "pydantic",
                "jwt": "PyJWT",
                "bcrypt": "bcrypt",
                "sqlite": "pysqlite3"
            }
            needed_packages = set()
            for mod in detected_modules:
                pkg = package_mapping.get(mod.lower(), mod)
                needed_packages.add(pkg)
            existing_packages = set()
            if os.path.exists(req_path):
                try:
                    with open(req_path, 'r', encoding='utf-8') as f_req:
                        for line in f_req:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                pkg_name = re.split(r'[=<>~]', line)[0].strip()
                                existing_packages.add(pkg_name.lower())
                except Exception:
                    pass
            missing = [pkg for pkg in needed_packages if pkg.lower() not in existing_packages]
            if missing:
                try:
                    with open(req_path, 'a', encoding='utf-8') as f_req:
                        for pkg in missing:
                            f_req.write(f"\n{pkg}")
                except Exception:
                    try:
                        with open(req_path, 'w', encoding='utf-8') as f_req:
                            for pkg in needed_packages:
                                f_req.write(f"{pkg}\n")
                    except Exception:
                        pass

    # ------------------------------------------------------------------ #
    # Self-healing: ESM/CommonJS, SQLite pragmas, hardcoded ports
    # ------------------------------------------------------------------ #
    @staticmethod
    def auto_heal_esm_commonjs():
        """Detect ESM vs CommonJS usage and fix ``"type"`` in package.json."""
        pkg_path = os.path.join(SysTools.WORKSPACE, "package.json")
        if not os.path.exists(pkg_path):
            return
        has_import = False
        has_require = False
        for root, _, files in os.walk(SysTools.WORKSPACE):
            if "node_modules" in root or ".git" in root or "venv" in root:
                continue
            for f in files:
                if f.endswith(('.js', '.jsx', '.ts', '.tsx')):
                    try:
                        with open(os.path.join(root, f), 'r', encoding='utf-8') as file_obj:
                            content = file_obj.read()
                        if re.search(r'^\s*import\s+[\'\"]|^\s*import\s+.*\s+from\s+[\'\"]', content, re.MULTILINE):
                            has_import = True
                        if re.search(r'\brequire\s*\(', content):
                            has_require = True
                    except Exception:
                        pass
        try:
            with open(pkg_path, 'r', encoding='utf-8') as f_pkg:
                pkg_data = json.load(f_pkg)
        except Exception:
            pkg_data = {}
        if not isinstance(pkg_data, dict):
            pkg_data = {}
        if has_import and not has_require:
            pkg_data["type"] = "module"
            print("📦 [SISTEMA] Proyecto detectado como ESM. Ajustando type=module en package.json.")
        elif has_require and not has_import:
            pkg_data["type"] = "commonjs"
            print("📦 [SISTEMA] Proyecto detectado como CommonJS. Ajustando type=commonjs en package.json.")
        try:
            with open(pkg_path, 'w', encoding='utf-8') as f_pkg:
                json.dump(pkg_data, f_pkg, indent=2)
        except Exception:
            pass

    @staticmethod
    def auto_heal_sqlite_connections():
        """Inject WAL + busy_timeout pragmas into Python/JS sqlite connections."""
        if not os.path.exists(SysTools.WORKSPACE):
            return
        for root, _, files_in_dir in os.walk(SysTools.WORKSPACE):
            if "node_modules" in root or ".git" in root or "venv" in root or "__pycache__" in root:
                continue
            for f in files_in_dir:
                if f.endswith('.py'):
                    path = os.path.join(root, f)
                    try:
                        with open(path, 'r', encoding='utf-8') as file_obj:
                            content = file_obj.read()
                        
                        # Idempotency check: don't double inject
                        if "journal_mode=WAL" in content:
                            continue
                            
                        # Matches start of line, indentation, connect statement and variable name
                        pattern = r'(^([ \t]*)((\w+)\s*=\s*sqlite3\.connect\([^\n]+))'

                        def repl_py(m):
                            indent = m.group(2)
                            line = m.group(3)
                            var_name = m.group(4)
                            return (f'{indent}{line}\n{indent}try:\n{indent}    {var_name}.execute("PRAGMA journal_mode=WAL")\n'
                                    f'{indent}    {var_name}.execute("PRAGMA busy_timeout=5000")\n{indent}except Exception: pass')

                        new_content, count = re.subn(pattern, repl_py, content, flags=re.MULTILINE)
                        if count > 0:
                            with open(path, 'w', encoding='utf-8') as file_obj:
                                file_obj.write(new_content)
                    except Exception:
                        pass
                elif f.endswith(('.js', '.ts')):
                    path = os.path.join(root, f)
                    try:
                        with open(path, 'r', encoding='utf-8') as file_obj:
                            content = file_obj.read()
                            
                        # Idempotency check
                        if "journal_mode=WAL" in content:
                            continue
                            
                        pattern = r'(\b(const|let|var)\s+(\w+)\s*=\s*new\s+sqlite3\.Database\([^\n]+)'

                        def repl_js(m):
                            line = m.group(1)
                            var_name = m.group(3)
                            return (f'{line}\n{var_name}.run("PRAGMA journal_mode=WAL;");\n'
                                    f'{var_name}.run("PRAGMA busy_timeout=5000;");')

                        new_content, count = re.subn(pattern, repl_js, content)
                        if count > 0:
                            with open(path, 'w', encoding='utf-8') as file_obj:
                                file_obj.write(new_content)
                    except Exception:
                        pass

    @staticmethod
    def auto_heal_hardcoded_ports():
        """Rewrite hardcoded ports to read the ``PORT`` environment variable."""
        if not os.path.exists(SysTools.WORKSPACE):
            return
        for root, _, files_in_dir in os.walk(SysTools.WORKSPACE):
            if "node_modules" in root or ".git" in root or "venv" in root or "__pycache__" in root:
                continue
            for f in files_in_dir:
                if f.endswith(('.js', '.jsx', '.ts', '.tsx')):
                    path = os.path.join(root, f)
                    try:
                        with open(path, 'r', encoding='utf-8') as file_obj:
                            content = file_obj.read()
                        new_content, count1 = re.subn(
                            r'\b(const|let|var)\s+PORT\s*=\s*(\d+)\s*;?',
                            r'\1 PORT = process.env.PORT || \2;',
                            content
                        )
                        new_content, count2 = re.subn(
                            r'\.listen\(\s*(\d+)\s*(,|\))',
                            r'.listen(process.env.PORT || \1\2',
                            new_content
                        )
                        new_content, count3 = re.subn(
                            r'http://localhost:\d+/api',
                            r'((typeof window !== "undefined" ? window.location.origin : "") + "/api")',
                            new_content
                        )
                        if count1 > 0 or count2 > 0 or count3 > 0:
                            with open(path, 'w', encoding='utf-8') as file_obj:
                                file_obj.write(new_content)
                    except Exception:
                        pass
                elif f.endswith('.py'):
                    path = os.path.join(root, f)
                    try:
                        with open(path, 'r', encoding='utf-8') as file_obj:
                            content = file_obj.read()
                        new_content, count = re.subn(
                            r'\bport\s*=\s*(\d+)',
                            r"port=int(os.environ.get('PORT', \1))",
                            content
                        )
                        if count > 0:
                            with open(path, 'w', encoding='utf-8') as file_obj:
                                file_obj.write(new_content)
                    except Exception:
                        pass

    # ------------------------------------------------------------------ #
    # File I/O: read, write (with critical-file interception), patch, parser
    # ------------------------------------------------------------------ #
    @staticmethod
    def read(name: str) -> str:
        """Read a workspace file by relative path (empty string if missing/binary)."""
        p = os.path.join(SysTools.WORKSPACE, name)
        if not os.path.exists(p):
            return ""
        try:
            with open(p, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            # Safely catch UnicodeDecodeError for binary files (e.g. SQLite databases)
            return ""
        except Exception:
            return ""

    @staticmethod
    def write(name: str, c: str, force: bool = False):
        """Write a file into the workspace.

        Critical files are intercepted (when ``state.interception_enabled`` and not
        ``force``) into ``state.pending_writes`` for user confirmation.

        Returns:
            The absolute path written, or ``"PENDING"`` when intercepted.
        """
        clean_name = name.lstrip("\\/")
        if ":" in clean_name:
            clean_name = clean_name.split(":", 1)[-1].lstrip("\\/")
        clean_name = os.path.normpath(clean_name)
        while clean_name.startswith("..") or clean_name.startswith("/") or clean_name.startswith("\\"):
            clean_name = clean_name.replace("../", "").replace("..\\", "").replace("..", "").lstrip("\\/")

        # Manifest block validation (SQUAD 2.0)
        manifest_path = os.path.join(SysTools.WORKSPACE, "build_manifest.json")
        if os.path.exists(manifest_path) and clean_name not in ["build_manifest.json", "SPEC.md", "ARCHITECTURE.md", "VISUAL_REPORT.md", "SECURITY_REPORT.md"]:
            try:
                import json
                with open(manifest_path, "r", encoding="utf-8") as f_manifest:
                    manifest_data = json.load(f_manifest)
                allowed_files = manifest_data.get("files", [])
                norm_clean = clean_name.replace('\\', '/')
                norm_allowed = [f.replace('\\', '/') for f in allowed_files]
                
                is_allowed = (
                    norm_clean in norm_allowed or 
                    any(norm_clean.startswith(f + "/") for f in norm_allowed) or
                    norm_clean.startswith(".github/") or
                    norm_clean.startswith("tests/") or
                    norm_clean.endswith("_test.py") or
                    norm_clean.endswith(".test.js") or
                    norm_clean == "schema.sql"
                )
                
                if not is_allowed:
                    state.launcher_logs.append(
                        f"🚫 [SISTEMA] Escritura BLOQUEADA para '{clean_name}' (No listado en build_manifest.json)."
                    )
                    return os.path.abspath(os.path.join(SysTools.WORKSPACE, clean_name))
            except Exception as e:
                print(f"Error validating manifest: {e}")

        # Shift-Left Syntax validation
        is_valid, err_msg = SysTools.check_syntax(clean_name, c)
        if not is_valid:
            SysTools.broken_memory_files[clean_name] = c
            state.launcher_logs.append(
                f"❌ [SHIFT-LEFT] Sintaxis inválida detectada en memoria para '{clean_name}': {err_msg}. Escritura bloqueada."
            )
            # Return absolute path to prevent pipeline crash, letting linter heal it later
            return os.path.abspath(os.path.join(SysTools.WORKSPACE, clean_name))
        
        # Clear previously registered broken content if now valid
        if clean_name in SysTools.broken_memory_files:
            SysTools.broken_memory_files.pop(clean_name)

        is_critical = clean_name in [
            "app.py", "package.json", "index.html", ".env", "docker-compose.yml",
            "requirements.txt", "main_output.py", "main_output.js", "main_output.tsx"
        ]
        if not force and getattr(state, "interception_enabled", True) and is_critical:
            if not hasattr(state, "pending_writes"):
                state.pending_writes = {}
            state.pending_writes[clean_name] = c
            state.launcher_logs.append(
                f"[INTERCEPTOR] ⚠️ Modificación de '{clean_name}' retenida para confirmación del usuario."
            )
            return "PENDING"

        p = os.path.abspath(os.path.join(SysTools.WORKSPACE, clean_name))
        if not p.startswith(os.path.abspath(SysTools.WORKSPACE)):
            p = os.path.join(SysTools.WORKSPACE, "fallback_unnamed_file.txt")

        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(c)
        if hasattr(state, "file_changes"):
            state.file_changes.append(clean_name)
        return p

    @staticmethod
    def apply_patch(file_path_rel: str, patch_text: str) -> bool:
        """Apply a ``<<<<<<< SEARCH / ======= / >>>>>>> END`` patch to a file."""
        p = os.path.abspath(os.path.join(SysTools.WORKSPACE, file_path_rel.lstrip("\\/")))
        if not p.startswith(os.path.abspath(SysTools.WORKSPACE)):
            return False

        content = ""
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                return False
        else:
            try:
                os.makedirs(os.path.dirname(p), exist_ok=True)
                parts = patch_text.split("<<<<<<< SEARCH")
                replace_content = []
                for part in parts[1:]:
                    if "=======" not in part or ">>>>>>> END" not in part:
                        continue
                    _, rest = part.split("=======", 1)
                    replace_block, _ = rest.split(">>>>>>> END", 1)
                    replace_content.append(replace_block.strip("\r\n"))
                final_content = "\n".join(replace_content)
                with open(p, "w", encoding="utf-8") as f:
                    f.write(final_content)
                return True
            except Exception:
                return False

        parts = patch_text.split("<<<<<<< SEARCH")
        modified = False
        for part in parts[1:]:
            if "=======" not in part or ">>>>>>> END" not in part:
                continue
            search_block, rest = part.split("=======", 1)
            replace_block, _ = rest.split(">>>>>>> END", 1)

            search_block = search_block.strip("\r\n")
            replace_block = replace_block.strip("\r\n")

            if not search_block:
                continue

            if search_block in content:
                content = content.replace(search_block, replace_block)
                modified = True
            else:
                search_lines = [l.rstrip() for l in search_block.splitlines()]
                content_lines = [l.rstrip() for l in content.splitlines()]
                search_len = len(search_lines)
                for idx in range(len(content_lines) - search_len + 1):
                    if content_lines[idx:idx + search_len] == search_lines:
                        replace_lines = [l.rstrip() for l in replace_block.splitlines()]
                        content_lines[idx:idx + search_len] = replace_lines
                        content = "\n".join(content_lines)
                        modified = True
                        break
        if modified:
            with open(p, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        return False

    @staticmethod
    def dry_parse_multifile(text: str) -> Dict[str, str]:
        """Preview-parse ``@@FILE:``/``@@ENDFILE@@`` blocks without writing to disk."""
        lines = text.split("\n")
        current_file = None
        current_content = []
        files = {}
        for line in lines:
            if line.startswith("@@FILE:"):
                if current_file:
                    files[current_file] = "\n".join(current_content).strip("`\n ")
                current_file = line.replace("@@FILE:", "").strip()
                current_content = []
            elif line.startswith("@@ENDFILE@@") or line.startswith("@@ENDFILE"):
                if current_file:
                    files[current_file] = "\n".join(current_content).strip("`\n ")
                    current_file = None
            else:
                if current_file is not None:
                    if line.strip().startswith("```") and len(line.strip()) <= 15:
                        continue
                    current_content.append(line)
        if current_file:
            files[current_file] = "\n".join(current_content).strip("`\n ")
        return files

    @staticmethod
    def extract_multifile_in_memory(text: str) -> Dict[str, str]:
        """Extract @@FILE: blocks in memory without writing to disk.

        Returns:
            Dict mapping filename to file content.
        """
        lines = text.split("\n")
        current_file = None
        current_content = []
        files = {}

        for line in lines:
            if line.startswith("@@FILE:"):
                if current_file:
                    files[current_file] = "\n".join(current_content).strip("`\n ")
                current_file = line.replace("@@FILE:", "").strip()
                current_content = []
                continue
            elif line.startswith("@@PATCH:") or line.startswith("@@DELETE:") or line.startswith("@@ENDFILE") or line.startswith("@@ENDPATCH"):
                if current_file:
                    files[current_file] = "\n".join(current_content).strip("`\n ")
                    current_file = None
                continue

            if current_file is not None:
                if line.strip().startswith("```") and len(line.strip()) <= 15:
                    continue
                current_content.append(line)

        if current_file:
            files[current_file] = "\n".join(current_content).strip("`\n ")

        # Fallback: Parse standard Markdown code blocks if no @@FILE: tags were found (SQUAD 2.0 Robustness)
        if not files:
            import re
            # Find all markdown code blocks: ```[lang]\n[content]\n```
            blocks = re.findall(r'```(\w*)\n(.*?)\n```', text, re.DOTALL)
            
            # Find all mentions of filenames in the text
            file_mentions = re.findall(r'([\w\/\.\-_]+\.(?:py|js|html|css|sql|ejs))', text)
            known_files = ["main_output.py", "app.py", "server.js", "index.html", "styles.css", "schema.sql", "index.ejs", "package.json", "requirements.txt"]
            valid_mentions = [m for m in file_mentions if any(kf in m for kf in known_files)]
            
            if len(blocks) == 1 and len(valid_mentions) == 1:
                target_file = os.path.basename(valid_mentions[0])
                files[target_file] = blocks[0][1].strip("`\n ")
            else:
                for lang, content in blocks:
                    content_clean = content.strip("`\n ")
                    first_line = content_clean.splitlines()[0] if content_clean else ""
                    match_filename = re.search(r'(?:#|//|<!--)\s*([\w\.\-_]+\.(?:py|js|html|css|sql|ejs))', first_line)
                    if match_filename:
                        files[match_filename.group(1)] = content_clean
                    else:
                        if lang in ['py', 'python'] or 'import ' in content_clean or 'def ' in content_clean:
                            if 'streamlit' in content_clean or 'st.' in content_clean:
                                files['app.py'] = content_clean
                            else:
                                files['main_output.py'] = content_clean
                        elif lang in ['html', 'xml'] or '<html' in content_clean or '<div' in content_clean:
                            files['index.html'] = content_clean
                        elif lang in ['css'] or 'body {' in content_clean or 'margin:' in content_clean:
                            files['styles.css'] = content_clean
                        elif lang in ['sql'] or 'CREATE TABLE' in content_clean:
                            files['schema.sql'] = content_clean
                        elif lang in ['js', 'javascript'] or 'const ' in content_clean or 'require(' in content_clean:
                            files['server.js'] = content_clean

        return files

    @staticmethod
    def extract_and_write_multifile(text: str) -> List[str]:
        """Parse and execute ``@@FILE:``/``@@PATCH:``/``@@DELETE:`` operations from LLM output.

        Returns:
            List of created/modified file names.
        """
        lines = text.split("\n")
        current_file = None
        current_content = []
        files = []
        current_patch_file = None
        current_patch_content = []

        for line in lines:
            if line.startswith("@@PATCH:"):
                if current_file:
                    SysTools.write(current_file, "\n".join(current_content).strip("`\n "))
                    current_file = None
                if current_patch_file:
                    SysTools.apply_patch(current_patch_file, "\n".join(current_patch_content))
                    current_patch_file = None
                current_patch_file = line.replace("@@PATCH:", "").strip()
                current_patch_content = []
                files.append(current_patch_file)
                continue
            elif line.startswith("@@FILE:"):
                if current_file:
                    SysTools.write(current_file, "\n".join(current_content).strip("`\n "))
                if current_patch_file:
                    SysTools.apply_patch(current_patch_file, "\n".join(current_patch_content))
                    current_patch_file = None
                current_file = line.replace("@@FILE:", "").strip()
                current_content = []
                files.append(current_file)
                continue
            elif line.startswith("@@DELETE:"):
                if current_file:
                    SysTools.write(current_file, "\n".join(current_content).strip("`\n "))
                    current_file = None
                if current_patch_file:
                    SysTools.apply_patch(current_patch_file, "\n".join(current_patch_content))
                    current_patch_file = None
                del_file = line.replace("@@DELETE:", "").strip()
                del_path = os.path.abspath(os.path.join(SysTools.WORKSPACE, del_file.lstrip("\\/")))
                if del_path.startswith(os.path.abspath(SysTools.WORKSPACE)) and os.path.exists(del_path):
                    try:
                        os.remove(del_path)
                    except Exception:
                        pass
                continue

            has_endfile = "@@ENDFILE" in line
            has_endpatch = "@@ENDPATCH" in line

            if has_endfile or has_endpatch:
                tag = "@@ENDFILE" if has_endfile else "@@ENDPATCH"
                parts = line.split(tag, 1)
                before_tag = parts[0]
                before_tag = before_tag.replace(">>>>>>> END", "").rstrip()

                if current_file is not None:
                    if before_tag.strip():
                        if not (before_tag.strip().startswith("```") and len(before_tag.strip()) <= 15):
                            current_content.append(before_tag)
                    SysTools.write(current_file, "\n".join(current_content).strip("`\n "))
                    current_file = None
                elif current_patch_file is not None:
                    if before_tag.strip():
                        current_patch_content.append(before_tag)
                    SysTools.apply_patch(current_patch_file, "\n".join(current_patch_content))
                    current_patch_file = None
                continue

            if current_file is not None:
                if line.strip().startswith("```") and len(line.strip()) <= 15:
                    continue
                current_content.append(line)
            elif current_patch_file is not None:
                current_patch_content.append(line)

        if current_file:
            SysTools.write(current_file, "\n".join(current_content).strip("`\n "))
        if current_patch_file:
            SysTools.apply_patch(current_patch_file, "\n".join(current_patch_content))

        if not files:
            # Fallback: parse fenced code blocks when no @@FILE markers present (SQUAD 2.0 Stack-Aware Fallback)
            import json
            current_stack = "FASTAPI_HTMX"
            manifest_path = os.path.join(SysTools.WORKSPACE, "build_manifest.json")
            if os.path.exists(manifest_path):
                try:
                    with open(manifest_path, "r", encoding="utf-8") as f_manifest:
                        manifest_data = json.load(f_manifest)
                    current_stack = manifest_data.get("stack", "FASTAPI_HTMX")
                except Exception:
                    pass

            blocks = re.findall(r'```([a-zA-Z0-9_-]*)\s*(.*?)(?:```|$)', text, re.DOTALL)
            if not blocks:
                return []

            for lang_tag, code in blocks:
                lang_tag = lang_tag.lower()
                code_clean = code.strip("`\n ")
                fname = None

                # Check if the code block starts with a comment specifying the filename
                first_lines = [line.strip() for line in code_clean.splitlines()[:2]]
                for line in first_lines:
                    m = re.search(r'(?:#|//|/\*|<!--)\s*@FILE:?\s*([a-zA-Z0-9_\-\./]+)', line, re.IGNORECASE)
                    if m:
                        fname = m.group(1).strip()
                        break

                if not fname:
                    if current_stack == "FASTAPI_HTMX":
                        if lang_tag in ["py", "python", "py3"]:
                            fname = "main_output.py"
                        elif lang_tag in ["html", "xml"] or "<html" in code_clean.lower() or "<div" in code_clean.lower():
                            fname = "index.html"
                        elif lang_tag in ["css"] or "body {" in code_clean or "margin:" in code_clean:
                            fname = "styles.css"
                        elif lang_tag in ["sql"] or "CREATE TABLE" in code_clean:
                            fname = "schema.sql"
                    elif current_stack == "NODE_EJS":
                        if lang_tag in ["js", "javascript"]:
                            is_server = "express" in code_clean or "require(" in code_clean or "listen(" in code_clean
                            fname = "server.js" if is_server else "public/app.js"
                        elif lang_tag in ["html", "ejs"] or "<html" in code_clean.lower() or "<div" in code_clean.lower():
                            fname = "views/index.ejs"
                        elif lang_tag in ["css"] or "body {" in code_clean or "margin:" in code_clean:
                            fname = "public/styles.css"
                        elif lang_tag in ["sql"] or "CREATE TABLE" in code_clean:
                            fname = "schema.sql"
                    elif current_stack == "PYTHON_STREAMLIT":
                        if lang_tag in ["py", "python"]:
                            fname = "app.py"

                if fname:
                    SysTools.write(fname, code_clean)
                    files.append(fname)
        return files

    @staticmethod
    def extract_code(text: str) -> str:
        """Pull the first fenced code block out of a response, else return trimmed text."""
        m = re.search(r'```[a-zA-Z0-9_-]*\s*(.*?)\s*```', text, re.DOTALL)
        return m.group(1).strip() if m else text.strip()

    # ------------------------------------------------------------------ #
    # Syntax checking, bracket balancing, CSS auto-fix, linter
    # ------------------------------------------------------------------ #
    @staticmethod
    def check_syntax(name: str, c: str) -> Tuple[bool, str]:
        """Quick in-memory syntax check for a file by extension."""
        if name.endswith('.py'):
            try:
                # 1. Compile check
                compile(c, name, 'exec')
                
                # 2. Local import validation check (SQUAD 2.0 Shift-Left Imports)
                import ast
                import sys
                
                std_libs = set(sys.builtin_module_names)
                common_libs = {"fastapi", "uvicorn", "jinja2", "streamlit", "sqlite3", "pydantic", "sqlalchemy", "requests", "bs4", "pandas", "numpy"}
                
                tree = ast.parse(c, filename=name)
                for node in ast.walk(tree):
                    imported_module = None
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imported_module = alias.name
                    elif isinstance(node, ast.ImportFrom):
                        imported_module = node.module
                    
                    if imported_module:
                        base_module = imported_module.split('.')[0]
                        if base_module not in std_libs and base_module not in common_libs:
                            local_py_file = base_module + ".py"
                            local_dir = base_module
                            
                            path_py = os.path.join(SysTools.WORKSPACE, local_py_file)
                            path_dir = os.path.join(SysTools.WORKSPACE, local_dir)
                            if not os.path.exists(path_py) and not os.path.exists(path_dir):
                                allowed = False
                                manifest_path = os.path.join(SysTools.WORKSPACE, "build_manifest.json")
                                if os.path.exists(manifest_path):
                                    try:
                                        import json
                                        with open(manifest_path, "r", encoding="utf-8") as f_manifest:
                                            m_data = json.load(f_manifest)
                                        allowed_files = m_data.get("files", [])
                                        if any(base_module in f for f in allowed_files):
                                            allowed = True
                                    except Exception:
                                        pass
                                
                                if not allowed:
                                    return False, f"ImportError: El archivo intenta importar el módulo local '{imported_module}' que no existe en el workspace ni está permitido en build_manifest.json. Todo el código debe ser autocontenido en {name}."
                
                return True, ""
            except SyntaxError as e:
                return False, f"SyntaxError: {e.msg} en la línea {e.lineno}"
            except Exception as e:
                return False, str(e)
        elif name.endswith(('.js', '.jsx', '.ts', '.tsx')):
            if shutil.which('node'):
                import tempfile
                temp_f_name = None
                try:
                    suffix = os.path.splitext(name)[1]
                    with tempfile.NamedTemporaryFile(suffix=suffix, mode='w', encoding='utf-8', delete=False) as temp_f:
                        temp_f.write(c)
                        temp_f_name = temp_f.name
                    res = subprocess.run(['node', '--check', temp_f_name], capture_output=True, text=True)
                    os.remove(temp_f_name)
                    if res.returncode != 0:
                        err = res.stderr.replace(temp_f_name, name)
                        return False, err.strip()
                    return True, ""
                except Exception:
                    try:
                        if temp_f_name:
                            os.remove(temp_f_name)
                    except Exception:
                        pass
        return True, ""

    @staticmethod
    def check_brackets_and_quotes(content: str) -> Tuple[bool, str]:
        """String-aware bracket/quote balance checker (py/js/css/ts/html)."""
        stack = []
        mapping = {')': '(', '}': '{', ']': '['}
        lines = content.splitlines()
        in_block_comment = False
        in_string = None

        for line_idx, line in enumerate(lines):
            col_idx = 0
            while col_idx < len(line):
                char = line[col_idx]

                if not in_string and not in_block_comment:
                    if line[col_idx:col_idx + 2] == '//':
                        break
                    if line[col_idx:col_idx + 2] == '/*':
                        in_block_comment = True
                        col_idx += 2
                        continue
                if in_block_comment:
                    if line[col_idx:col_idx + 2] == '*/':
                        in_block_comment = False
                        col_idx += 2
                    else:
                        col_idx += 1
                    continue

                if in_string:
                    if char == '\\':
                        col_idx += 2
                        continue
                    if char == in_string:
                        in_string = None
                    col_idx += 1
                    continue
                else:
                    if char in ('"', "'", '`'):
                        in_string = char
                        col_idx += 1
                        continue

                if char in ('(', '{', '['):
                    stack.append((char, line_idx + 1))
                elif char in (')', '}', ']'):
                    if not stack:
                        return False, f"Cierre inesperado '{char}' en línea {line_idx + 1}"
                    top, start_line = stack.pop()
                    if mapping[char] != top:
                        return (False, f"Se esperaba el cierre de '{top}' (abierto en línea {start_line}) "
                                       f"pero se encontró '{char}' en línea {line_idx + 1}")
                col_idx += 1

        if stack:
            top, start_line = stack[-1]
            return False, f"Apertura de '{top}' en línea {start_line} no está cerrada."
        return True, "Correcto"

    @staticmethod
    def auto_fix_css(file_path: str, content: str) -> bool:
        """Deterministically append missing ``)``/``}`` to broken CSS.

        Returns:
            True if the file was modified.
        """
        lines = content.splitlines()
        fixed_lines = []
        open_parens = 0
        open_braces = 0
        in_string = None
        changed = False
        for line in lines:
            for ch in line:
                if in_string:
                    if ch == in_string:
                        in_string = None
                elif ch in ('"', "'"):
                    in_string = ch
                elif ch == '(':
                    open_parens += 1
                elif ch == ')':
                    if open_parens > 0:
                        open_parens -= 1
                elif ch == '{':
                    open_braces += 1
                elif ch == '}':
                    if open_braces > 0:
                        open_braces -= 1
            fixed_lines.append(line)
        if open_parens > 0:
            fixed_lines[-1] = fixed_lines[-1] + (')' * open_parens)
            changed = True
        if open_braces > 0:
            fixed_lines.append('}' * open_braces)
            changed = True
        if changed:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(fixed_lines))
            except Exception:
                pass
        return changed

    @staticmethod
    def run_linter(file_path: str) -> Tuple[bool, str]:
        """Multi-language linter with auto-repair.

        Handles Python (py_compile), CSS (bracket check + auto-fix) and JS/TS/HTML
        (bracket check, duplicate-const removal, optional ``node --check``).
        """
        # Check if we have a broken version in memory for this file (Shift-Left)
        rel_path = os.path.relpath(file_path, SysTools.WORKSPACE).replace('\\', '/')
        if rel_path in SysTools.broken_memory_files:
            content = SysTools.broken_memory_files[rel_path]
            ok, err_msg = SysTools.check_syntax(rel_path, content)
            if not ok:
                return False, err_msg

        content = ""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return False, f"No se pudo leer el archivo: {e}"

        if file_path.endswith('.py'):
            stripped = content.strip()
            # Guard: env var file (KEY=value format, not Python) → delete it
            env_var_pattern = bool(re.match(r'^[A-Z_][A-Z0-9_]*=[^\s]', stripped))
            only_env_lines = all(
                re.match(r'^[A-Z_][A-Z0-9_]*=', l.strip()) or not l.strip() or l.strip().startswith('#')
                for l in stripped.splitlines()
            )
            if env_var_pattern and only_env_lines:
                try:
                    os.remove(file_path)
                except Exception:
                    pass
                return True, "Archivo de variables de entorno eliminado (no es Python válido)."

            # Guard: YAML content → rename
            yaml_indicators = (
                stripped.startswith(("name:", "on:", "jobs:", "steps:", "- name:"))
                or "runs-on:" in stripped
                or bool(re.search(r'^name:\s+\S', stripped, re.MULTILINE))
            )
            if yaml_indicators:
                new_path = re.sub(r'\.py$', '.yml', file_path)
                try:
                    os.rename(file_path, new_path)
                except Exception:
                    pass
                return True, "Archivo YAML renombrado de .py a .yml correctamente."

            # Guard: Markdown content → rename
            markdown_indicators = (
                stripped.startswith(("- ", "* ", "1. ", "2. ", "3. ", "### ", "# ", "## ", "---"))
                or "**" in stripped or "###" in stripped or "####" in stripped
            )
            if markdown_indicators:
                new_path = re.sub(r'\.py$', '.md', file_path)
                try:
                    os.rename(file_path, new_path)
                except Exception:
                    pass
                return True, "Archivo Markdown renombrado de .py a .md correctamente."
            try:
                subprocess.run([sys.executable, "-m", "py_compile", file_path],
                               check=True, capture_output=True, text=True)
                return True, "Síntaxis correcta."
            except subprocess.CalledProcessError as e:
                return False, e.stderr
        elif file_path.endswith('.css'):
            ok, msg = SysTools.check_brackets_and_quotes(content)
            if not ok:
                fixed = SysTools.auto_fix_css(file_path, content)
                if fixed:
                    return True, "CSS auto-reparado (paréntesis/llaves cerradas)."
                return False, msg
            return True, "Sintaxis CSS correcta."
        elif file_path.endswith(('.js', '.jsx', '.ts', '.tsx', '.html')):
            # Auto-fix JS: remove duplicate const declarations at end of file
            if file_path.endswith('.js') and not file_path.endswith(('.jsx', '.tsx')):
                lines = content.splitlines()
                declared_consts = {}
                clean_lines = []
                skip_block = False
                for i, line in enumerate(lines):
                    m = re.match(r'\s*(const|let|var)\s+(\w+)\s*=', line)
                    if m:
                        name = m.group(2)
                        if name in declared_consts:
                            skip_block = True
                            continue
                        else:
                            declared_consts[name] = i
                    elif skip_block and line.strip() == '});':
                        skip_block = False
                        continue
                    if not skip_block:
                        clean_lines.append(line)
                fixed_js = '\n'.join(clean_lines)
                if fixed_js != content:
                    try:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(fixed_js)
                        content = fixed_js
                    except Exception:
                        pass
            ok, msg = SysTools.check_brackets_and_quotes(content)
            if not ok:
                return False, msg
            if file_path.endswith('.js') and not file_path.endswith(('.jsx', '.tsx')):
                try:
                    subprocess.run(["node", "--check", file_path], check=True, capture_output=True, text=True)
                    return True, "Sintaxis de Node.js correcta."
                except subprocess.CalledProcessError as e:
                    return False, e.stderr + "\n" + e.stdout
                except FileNotFoundError:
                    pass
            return True, "Sintaxis balanceada."
        return True, "Linter skip"

    # ------------------------------------------------------------------ #
    # Web search
    # ------------------------------------------------------------------ #
    @staticmethod
    def web_search(query: str) -> str:
        """DuckDuckGo HTML scrape returning the top snippets."""
        import urllib.request
        import urllib.parse
        try:
            url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(query)
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req, timeout=10) as r:
                html = r.read().decode('utf-8')
                snippets = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', html, re.IGNORECASE | re.DOTALL)
                clean = [re.sub(r'<[^>]+>', '', s).strip() for s in snippets][:3]
                return "\n".join(clean) if clean else "No hay resultados útiles."
        except Exception as e:
            return f"Error de búsqueda: {e}"

    # ------------------------------------------------------------------ #
    # Git operations
    # ------------------------------------------------------------------ #
    @staticmethod
    def git_init_and_commit(msg: str = "Auto-commit") -> Tuple[bool, str]:
        """Shadow Git: init/config/add/commit inside the workspace under ``git_lock``."""
        with SysTools.git_lock:
            try:
                res = subprocess.run(
                    ["git", "rev-parse", "--is-inside-work-tree"],
                    cwd=SysTools.WORKSPACE, capture_output=True, text=True
                )
                is_git = (res.returncode == 0)
                if not is_git:
                    git_dir = os.path.join(SysTools.WORKSPACE, ".git")
                    if os.path.exists(git_dir):
                        shutil.rmtree(git_dir, ignore_errors=True)
                    subprocess.run(["git", "init"], cwd=SysTools.WORKSPACE, check=True, capture_output=True)
                    subprocess.run(["git", "config", "user.name", "Squad AI"], cwd=SysTools.WORKSPACE, check=True, capture_output=True)
                    subprocess.run(["git", "config", "user.email", "squad@ai.local"], cwd=SysTools.WORKSPACE, check=True, capture_output=True)
                subprocess.run(["git", "add", "."], cwd=SysTools.WORKSPACE, check=True, capture_output=True)
                subprocess.run(["git", "commit", "-m", msg], cwd=SysTools.WORKSPACE, capture_output=True)
                return True, "Shadow Git Commit Guardado."
            except Exception as e:
                return False, str(e)

    @staticmethod
    def git_push(repo_url: str, branch: str = "main") -> Tuple[bool, str]:
        """Set the remote origin and push to the given repo under ``git_lock``."""
        with SysTools.git_lock:
            try:
                subprocess.run(["git", "remote", "remove", "origin"], cwd=SysTools.WORKSPACE, capture_output=True)
                subprocess.run(["git", "remote", "add", "origin", repo_url], cwd=SysTools.WORKSPACE, check=True, capture_output=True)
                subprocess.run(["git", "branch", "-M", branch], cwd=SysTools.WORKSPACE, check=True, capture_output=True)
                subprocess.run(["git", "push", "-u", "origin", branch], cwd=SysTools.WORKSPACE, check=True, capture_output=True, text=True)
                return True, f"Push exitoso a {repo_url}"
            except subprocess.CalledProcessError as e:
                return False, f"Git error (Verifica autenticación/URL): {e.stderr}"
            except Exception as e:
                return False, str(e)

    # ------------------------------------------------------------------ #
    # Generic command runner & workspace stats
    # ------------------------------------------------------------------ #
    @staticmethod
    def run_command(cmd: List[str], cwd: Optional[str] = None, timeout: int = 300) -> Tuple[int, str, str]:
        """Run a shell command and capture output.

        Returns:
            Tuple of (return_code, stdout, stderr).
        """
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

    @staticmethod
    def get_workspace_stats() -> Dict[str, Any]:
        """Get statistics about the workspace (file counts, total size)."""
        stats = {
            "total_files": 0, "total_size_bytes": 0,
            "python_files": 0, "js_files": 0, "other_files": 0
        }
        if not os.path.exists(SysTools.WORKSPACE):
            return stats
        for root, _, files in os.walk(SysTools.WORKSPACE):
            skip_dirs = {"node_modules", ".git", "venv", "__pycache__"}
            if any(skip_dir in root for skip_dir in skip_dirs):
                continue
            for f in files:
                filepath = os.path.join(root, f)
                try:
                    stats["total_files"] += 1
                    stats["total_size_bytes"] += os.path.getsize(filepath)
                    if f.endswith('.py'):
                        stats["python_files"] += 1
                    elif f.endswith(('.js', '.jsx', '.ts', '.tsx')):
                        stats["js_files"] += 1
                    else:
                        stats["other_files"] += 1
                except Exception:
                    pass
        return stats
