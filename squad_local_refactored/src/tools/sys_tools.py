"""System tools: workspace management, dependency detection, Git operations, and code execution."""

import os
import sys
import json
import re
import subprocess
import threading
from typing import List, Optional, Tuple, Dict, Any

from ..core.config import settings


class SysTools:
    """System utilities for workspace management and code execution.
    
    This class provides:
    - Workspace setup and virtual environment management
    - Automatic dependency detection for Python and Node.js
    - Git operations with proper locking
    - Code execution in isolated environments
    - File and directory operations
    """
    
    WORKSPACE = settings.workspace
    git_lock = threading.Lock()

    @staticmethod
    def setup():
        """Initialize the workspace directory."""
        if not os.path.exists(SysTools.WORKSPACE):
            os.makedirs(SysTools.WORKSPACE)

    @staticmethod
    def setup_venv(logger_list: Optional[List[str]] = None) -> Tuple[str, str]:
        """Set up a Python virtual environment in the workspace.
        
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
                    check=True,
                    capture_output=True
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

        # Scan workspace for JS/TS files
        if os.path.exists(SysTools.WORKSPACE):
            for root, _, files_in_dir in os.walk(SysTools.WORKSPACE):
                # Skip common non-source directories
                skip_dirs = {"node_modules", ".git", "venv", "__pycache__"}
                if any(skip_dir in root for skip_dir in skip_dirs):
                    continue
                    
                for f in files_in_dir:
                    if f.endswith(('.js', '.jsx', '.ts', '.tsx')):
                        filepath = os.path.join(root, f)
                        try:
                            with open(filepath, 'r', encoding='utf-8') as file_obj:
                                content = file_obj.read()
                            
                            # Extract require() imports
                            req_matches = re.findall(
                                r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
                                content
                            )
                            
                            # Extract import statements
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

                            # Process dependencies
                            for dep in all_matches:
                                dep = dep.strip()
                                if not dep:
                                    continue
                                # Skip relative imports
                                if dep.startswith('.') or dep.startswith('/') or dep.startswith('\\'):
                                    continue

                                # Handle scoped packages
                                if dep.startswith('@'):
                                    parts = dep.split('/')
                                    dep_name = f"{parts[0]}/{parts[1]}" if len(parts) >= 2 else dep
                                else:
                                    dep_name = dep.split('/')[0]

                                if dep_name not in node_builtins:
                                    detected_deps.add(dep_name)
                        except Exception:
                            pass

        # Load existing package.json
        pkg_data = {}
        if os.path.exists(pkg_path):
            try:
                with open(pkg_path, 'r', encoding='utf-8') as f_pkg:
                    pkg_data = json.load(f_pkg)
            except Exception:
                pass

        if not isinstance(pkg_data, dict):
            pkg_data = {}

        # Set defaults
        pkg_data.setdefault("name", "squad-workspace-project")
        pkg_data.setdefault("type", "commonjs")
        
        # Ensure scripts section exists
        if "scripts" not in pkg_data or not isinstance(pkg_data["scripts"], dict):
            pkg_data["scripts"] = {}

        # Determine main entry point
        workspace_files = (
            os.listdir(SysTools.WORKSPACE)
            if os.path.exists(SysTools.WORKSPACE)
            else []
        )
        main_files = [
            f for f in workspace_files
            if f.startswith("main_output.") and f.endswith(('.js', '.ts', '.jsx', '.tsx'))
        ]
        target_f = main_files[0] if main_files else "main_output.js"
        
        # Check for common alternatives
        if not main_files:
            commons = [f for f in ["server.js", "app.js", "index.js", "main.js"] if f in workspace_files]
            if commons:
                target_f = commons[0]

        correct_start_cmd = f"node {target_f}"

        # Fix invalid start scripts
        current_start = pkg_data["scripts"].get("start", "")
        is_invalid = (
            not current_start
            or ".bat" in current_start
            or ".sh" in current_start
            or ".py" in current_start
            or ".md" in current_start
        )
        if is_invalid:
            pkg_data["scripts"]["start"] = correct_start_cmd

        # Ensure dependencies section exists
        if "dependencies" not in pkg_data or not isinstance(pkg_data["dependencies"], dict):
            pkg_data["dependencies"] = {}
        
        # Add detected dependencies
        for dep in detected_deps:
            if dep not in pkg_data["dependencies"]:
                pkg_data["dependencies"][dep] = "*"

        # Write updated package.json
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

        # Scan workspace for Python files
        if os.path.exists(SysTools.WORKSPACE):
            for root, _, files_in_dir in os.walk(SysTools.WORKSPACE):
                skip_dirs = {"node_modules", ".git", "venv", "__pycache__"}
                if any(skip_dir in root for skip_dir in skip_dirs):
                    continue
                    
                for f in files_in_dir:
                    if f.endswith('.py'):
                        filepath = os.path.join(root, f)
                        try:
                            with open(filepath, 'r', encoding='utf-8') as file_obj:
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

        # Map module names to package names
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
            mod_lower = mod.lower()
            if mod_lower in package_mapping:
                needed_packages.add(package_mapping[mod_lower])
            else:
                needed_packages.add(mod)

        # Load existing requirements
        existing_reqs = set()
        if os.path.exists(req_path):
            try:
                with open(req_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            # Extract package name (before == or other version specifiers)
                            pkg_name = line.split('==')[0].split('>=')[0].split('<=')[0].strip()
                            if pkg_name:
                                existing_reqs.add(pkg_name)
            except Exception:
                pass

        # Merge and write
        all_packages = existing_reqs.union(needed_packages)
        try:
            with open(req_path, 'w', encoding='utf-8') as f:
                for pkg in sorted(all_packages):
                    f.write(f"{pkg}\n")
        except Exception:
            pass

    @staticmethod
    def run_command(
        cmd: List[str],
        cwd: Optional[str] = None,
        timeout: int = 300
    ) -> Tuple[int, str, str]:
        """Run a shell command and capture output.
        
        Args:
            cmd: Command and arguments as a list.
            cwd: Working directory (defaults to workspace).
            timeout: Maximum execution time in seconds.
            
        Returns:
            Tuple of (return_code, stdout, stderr).
        """
        if cwd is None:
            cwd = SysTools.WORKSPACE
            
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
                env={**os.environ, "PYTHONIOENCODING": "utf-8"}
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            return -1, "", str(e)

    @staticmethod
    def get_workspace_stats() -> Dict[str, Any]:
        """Get statistics about the workspace.
        
        Returns:
            Dictionary with file counts, total size, etc.
        """
        stats = {
            "total_files": 0,
            "total_size_bytes": 0,
            "python_files": 0,
            "js_files": 0,
            "other_files": 0
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

    @staticmethod
    def read(file_path: str) -> str:
        """Read content of a file in the workspace.
        
        Args:
            file_path: Relative or absolute path to the file.
            
        Returns:
            File content as string.
        """
        # Handle relative paths
        if not os.path.isabs(file_path):
            full_path = os.path.join(SysTools.WORKSPACE, file_path)
        else:
            full_path = file_path
            
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()
