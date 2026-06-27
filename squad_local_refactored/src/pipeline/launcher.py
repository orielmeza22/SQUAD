"""Launcher engine and listening-port enumeration.

Migrated 1:1 from the legacy monolith ``run_launch_sequence`` and
``get_listening_ports``.
"""

import os
import re
import sys
import json
import time
import subprocess
from typing import Tuple, List, Dict, Any

import psutil

from ..core.state import state
from ..tools.sys_tools import SysTools
from . import self_heal


def get_listening_ports() -> List[Dict[str, Any]]:
    """Return a list of ``{port, pid, name}`` for all TCP LISTEN sockets."""
    ports: list = []
    if sys.platform == 'win32':
        try:
            out = subprocess.check_output("netstat -ano", shell=True, text=True)
            for line in out.splitlines():
                line = line.strip()
                if "LISTENING" in line:
                    parts = [x for x in line.split() if x]
                    if len(parts) >= 5:
                        local_addr = parts[1]
                        pid_str = parts[4]
                        port_part = local_addr.split(":")[-1]
                        try:
                            port = int(port_part)
                            pid = int(pid_str)
                            name = "Desconocido"
                            try:
                                name = psutil.Process(pid).name()
                            except Exception:
                                pass
                            ports.append({"port": port, "pid": pid, "name": name})
                        except Exception:
                            pass
        except Exception as e:
            print(f"Error parseando netstat: {e}")
    else:
        try:
            for conn in psutil.net_connections(kind='inet'):
                if conn.status == 'LISTEN':
                    port = conn.laddr.port
                    pid = conn.pid
                    name = "Desconocido"
                    if pid:
                        try:
                            name = psutil.Process(pid).name()
                        except Exception:
                            pass
                    ports.append({"port": port, "pid": pid, "name": name})
        except Exception:
            pass

    unique_ports = {}
    for p in ports:
        unique_ports[p['port']] = p
    return list(unique_ports.values())


def run_launch_sequence(model: str) -> Tuple[bool, str]:
    """Run the full launch sequence for the generated app.

    Performs: residual-process cleanup, SQLite backup, ESM/SQLite/port healing,
    pre-launch lint with autonomous repair, dependency detection, command
    selection (docker-compose/npm/python/http.server/Flask runner), port-collision
    resolution, ``subprocess.Popen`` and spawns the runtime watchdog.

    Args:
        model: LLM model to use for autonomous self-healing.

    Returns:
        Tuple of (success, message).
    """
    try:
        # 1. Clean residual files lock and processes in SQUAD_WORKSPACE
        state.launcher_logs.append("🧹 [SISTEMA] Liberando bloqueos de archivos y procesos residuales...")
        SysTools.cleanup_workspace_processes()

        # 2. SQLite old DB auto-backup if schema files changed
        schema_keywords = ["models.py", "schema.sql", "database.py", "db.py", "models.ts"]
        db_changed = any(any(kw in f for kw in schema_keywords) for f in getattr(state, "file_changes", []))
        if db_changed and os.path.exists(SysTools.WORKSPACE):
            for file_name in os.listdir(SysTools.WORKSPACE):
                if file_name.endswith(('.db', '.sqlite', '.sqlite3')):
                    db_path = os.path.join(SysTools.WORKSPACE, file_name)
                    backup_path = db_path + ".backup"
                    try:
                        if os.path.exists(db_path):
                            state.launcher_logs.append(f"📡 [SISTEMA] Cambios en el modelo de datos. Archivando DB vieja en: {backup_path}")
                            if os.path.exists(backup_path):
                                os.remove(backup_path)
                            os.rename(db_path, backup_path)
                    except Exception as ex:
                        state.launcher_logs.append(f"⚠️ [SISTEMA] Error al archivar base de datos: {ex}")

        # 3. Dynamic ESM/CommonJS healing
        state.launcher_logs.append("📦 [SISTEMA] Validando tipos CommonJS/ESM...")
        SysTools.auto_heal_esm_commonjs()

        # 4. SQLite WAL auto-injection
        state.launcher_logs.append("📡 [SISTEMA] Optimizando conexiones SQLite (WAL / busy_timeout)...")
        SysTools.auto_heal_sqlite_connections()

        # Pre-launch workspace syntax scan
        state.launcher_logs.append("🧹 [LINTER]: Verificando sintaxis de archivos en el workspace antes de lanzar...")
        syntax_errors: list = []
        if os.path.exists(SysTools.WORKSPACE):
            for root, _, files_in_dir in os.walk(SysTools.WORKSPACE):
                if ".git" in root or "node_modules" in root or "__pycache__" in root or "venv" in root:
                    continue
                for f in files_in_dir:
                    rel = os.path.relpath(os.path.join(root, f), SysTools.WORKSPACE).replace('\\', '/')
                    if rel.endswith(('.py', '.js', '.jsx', '.ts', '.tsx', '.html', '.css')):
                        ok, linter_msg = SysTools.run_linter(os.path.join(root, f))
                        if not ok:
                            syntax_errors.append(f"Archivo: {rel}\nError: {linter_msg}")
                            state.launcher_logs.append(f"⚠️ Error de Sintaxis en {rel}: {linter_msg}")

        if syntax_errors:
            state.launcher_logs.append("[LINTER] Detectados errores de sintaxis antes del lanzamiento.")
            err_details = syntax_errors[0]
            err_msg = err_details.split('\nError: ')[1] if '\nError: ' in err_details else err_details
            err_file = err_details.split('\nError: ')[0].replace('Archivo: ', '') if '\nError: ' in err_details else "unknown"
            err_line_match = re.search(r'línea (\d+)', err_details)
            err_line = err_line_match.group(1) if err_line_match else "1"

            state.active_diagnostic = {
                "error": err_msg,
                "file": err_file,
                "line": err_line,
                "suggestion": "El linter detectó un error. Por favor corrígelo o usa 'Auto-reparar con IA'."
            }

            if state.linter_retries < 3:
                state.linter_retries += 1
                state.launcher_logs.append(f"[LINTER AUTÓNOMO] 🔄 Intento de autoreparación {state.linter_retries}/3 en progreso...")
                self_heal.run_autonomous_linter(syntax_errors, model)
                state.launcher_logs.append("[LINTER AUTÓNOMO] 🚀 Re-intentando lanzamiento tras reparación...")
                import threading
                threading.Thread(target=run_launch_sequence, args=(model,), daemon=True).start()
                return True, "Iniciada autoreparación del linter."
            else:
                state.launcher_logs.append("⚠️ [LINTER AUTÓNOMO] Límite de autoreparación alcanzado. Lanzando de todas formas...")
        else:
            state.active_diagnostic = None

        if state.active_process and state.active_process.poll() is None:
            SysTools.kill_process_tree(state.active_process.pid)
            state.launcher_logs.append("[SISTEMA] Terminado el proceso local previo de raíz (árbol completo)...")

        # Git Auto-Snapshot
        SysTools.git_init_and_commit("Pre-run backup snapshot")

        state.launcher_logs.append("[SISTEMA] Arrancando secuencia de Launch...")

        # Setup dynamic virtual environment (venv)
        python_exe, pip_exe = SysTools.setup_venv(state.launcher_logs)

        # Auto-detect dependencies
        try:
            SysTools.auto_detect_nodejs_dependencies()
            SysTools.auto_detect_python_dependencies()
            SysTools.auto_heal_hardcoded_ports()
        except Exception as e:
            state.launcher_logs.append(f"⚠️ [SISTEMA] Error en auto-detección/autocuración: {e}")

        # Isolate workspace package.json from parent module scope if it doesn't exist
        pkg_path = os.path.join(SysTools.WORKSPACE, "package.json")
        if not os.path.exists(pkg_path):
            try:
                target_f = SysTools.find_node_entry_point()
                has_html = os.path.exists(os.path.join(SysTools.WORKSPACE, "index.html")) or os.path.exists(os.path.join(SysTools.WORKSPACE, "main_output.html"))
                
                is_node_backend = False
                target_path = os.path.join(SysTools.WORKSPACE, target_f)
                if os.path.exists(target_path):
                    with open(target_path, "r", encoding="utf-8") as f_target:
                        target_code = f_target.read()
                    if any(kw in target_code for kw in ["express", "http.createServer", "require('http')", "import http", "fastify", "koa", "app.listen"]):
                        is_node_backend = True

                if is_node_backend or not has_html:
                    start_cmd = f"node {target_f}"
                    with open(pkg_path, "w", encoding="utf-8") as f_pkg:
                        json.dump({
                            "name": "squad-workspace-project",
                            "type": "commonjs",
                            "scripts": {"start": start_cmd}
                        }, f_pkg, indent=2)
            except Exception:
                pass

        # Read stack from SPEC.md to select the run command
        stack = "FASTAPI_HTMX"
        spec_path = os.path.join(SysTools.WORKSPACE, "SPEC.md")
        if os.path.exists(spec_path):
            try:
                with open(spec_path, 'r', encoding='utf-8') as fspec:
                    spec_content = fspec.read()
                stack_match = re.search(r'STACK:\s*([A-Z0-9_]+)', spec_content)
                if stack_match:
                    stack = stack_match.group(1).strip()
                    state.launcher_logs.append(f"📦 [SISTEMA] Stack detectado en SPEC.md: {stack}")
            except Exception:
                pass

        if stack == "PYTHON_STREAMLIT":
            req_path = os.path.join(SysTools.WORKSPACE, "requirements.txt")
            if not os.path.exists(req_path):
                try:
                    with open(req_path, "w", encoding="utf-8") as freq:
                        freq.write("streamlit\n")
                except Exception:
                    pass
            cmd = f'"{pip_exe}" install --prefer-offline streamlit && "{python_exe}" -m streamlit run app.py --server.port 5000 --server.address 0.0.0.0'
        elif stack == "NODE_EJS":
            pkg_path = os.path.join(SysTools.WORKSPACE, "package.json")
            if not os.path.exists(pkg_path):
                try:
                    with open(pkg_path, "w", encoding="utf-8") as f_pkg:
                        json.dump({
                            "name": "squad-ejs-project",
                            "type": "commonjs",
                            "dependencies": {
                                "express": "^4.19.2",
                                "ejs": "^3.1.10",
                                "better-sqlite3": "^11.0.0"
                            },
                            "scripts": {"start": "node server.js"}
                        }, f_pkg, indent=2)
                except Exception:
                    pass
            cmd = "npm install --prefer-offline --no-audit --no-fund && npm start"
        elif stack == "FASTAPI_HTMX":
            req_path = os.path.join(SysTools.WORKSPACE, "requirements.txt")
            if not os.path.exists(req_path):
                try:
                    with open(req_path, "w", encoding="utf-8") as freq:
                        freq.write("fastapi\nuvicorn\njinja2\n")
                except Exception:
                    pass
            entry_file = "main_output.py" if os.path.exists(os.path.join(SysTools.WORKSPACE, "main_output.py")) else "app.py"
            if not os.path.exists(os.path.join(SysTools.WORKSPACE, entry_file)):
                entry_file = "main_output.py"
            cmd = f'"{pip_exe}" install --prefer-offline fastapi uvicorn jinja2 && "{python_exe}" {entry_file}'
        elif os.path.exists(os.path.join(SysTools.WORKSPACE, "docker-compose.yml")):
            cmd = "docker-compose up --build"
        elif os.path.exists(os.path.join(SysTools.WORKSPACE, "package.json")):
            cmd = "npm install --prefer-offline --no-audit --no-fund && npm start"
        elif os.path.exists(os.path.join(SysTools.WORKSPACE, "requirements.txt")):
            cmd = f'"{pip_exe}" install --prefer-offline -r requirements.txt && "{python_exe}" app.py'
        elif os.path.exists(os.path.join(SysTools.WORKSPACE, "app.py")):
            cmd = f'"{python_exe}" app.py'
        elif os.path.exists(os.path.join(SysTools.WORKSPACE, "index.html")) or os.path.exists(os.path.join(SysTools.WORKSPACE, "main_output.html")):
            html_path = os.path.join(SysTools.WORKSPACE, "index.html") or os.path.join(SysTools.WORKSPACE, "main_output.html")
            try:
                with open(html_path, 'r', encoding='utf-8') as _f:
                    _html_content = _f.read()
                _uses_jinja = '{{' in _html_content or '{%' in _html_content or 'url_for' in _html_content
            except Exception:
                _uses_jinja = False
            if _uses_jinja and os.path.exists(os.path.join(SysTools.WORKSPACE, "app.py")):
                cmd = f'"{python_exe}" app.py'
            elif _uses_jinja:
                # Generate a minimal Flask runner for Jinja2 templates
                state.launcher_logs.append("[SISTEMA] ⚠️ index.html usa Jinja2. Generando app.py mínimo de Flask...")
                minimal_flask = '''import os
from flask import Flask, send_from_directory, render_template

# template_folder and static_folder point to the workspace root
# so Flask finds index.html, styles.css, app.js etc. directly
app = Flask(
    __name__,
    template_folder=os.path.dirname(os.path.abspath(__file__)),
    static_folder=os.path.dirname(os.path.abspath(__file__)),
    static_url_path=""
)

@app.route("/")
def index():
    try:
        # Try rendering Jinja2 template if index.html uses template tags
        return render_template("index.html")
    except Exception:
        # Fallback to static serving if rendering fails (e.g. syntax errors in template)
        return app.send_static_file("index.html")

@app.route("/<path:filename>")
def static_files(filename):
    import os
    from flask import send_from_directory
    actual_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    if not os.path.exists(actual_path) and filename.startswith("static/"):
        stripped = filename.replace("static/", "", 1)
        if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), stripped)):
            filename = stripped
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), filename)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, port=port)
'''
                _app_path = os.path.join(SysTools.WORKSPACE, "app.py")
                os.makedirs(os.path.dirname(_app_path), exist_ok=True)
                with open(_app_path, "w", encoding="utf-8") as _fapp:
                    _fapp.write(minimal_flask)
                cmd = f'"{pip_exe}" install --prefer-offline flask && "{python_exe}" app.py'
            else:
                cmd = f'"{python_exe}" -m http.server 5000'
        else:
            workspace_files = os.listdir(SysTools.WORKSPACE) if os.path.exists(SysTools.WORKSPACE) else []
            main_files = [f for f in workspace_files if f.startswith("main_output.")]

            target_file = None
            if main_files:
                main_files.sort(key=lambda x: (
                    0 if x == "main_output.py" else
                    1 if x == "main_output.js" else
                    2 if x.endswith((".sh", ".bat", ".cmd")) else
                    3
                ))
                target_file = main_files[0]

            if target_file:
                target_path = os.path.join(SysTools.WORKSPACE, target_file)
                with open(target_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()

                lines = content.splitlines()
                if lines and lines[0].strip().lower() in ("bash", "sh", "console", "terminal", "intento", "json", "python", "js", "ts", "tsx", "html", "css"):
                    lines = lines[1:]
                content = "\n".join(lines).strip().replace("```bash", "").replace("```", "").strip()

                is_script = False
                if target_file.endswith((".sh", ".bat", ".cmd")):
                    is_script = True
                elif target_file.endswith((".js", ".py", ".ts", ".tsx", ".html", ".css", ".json", ".sql", ".md")):
                    is_script = False
                elif "npx " in content or "npm " in content:
                    is_script = True
                elif "import " not in content and "print" not in content and content:
                    is_script = True

                if is_script:
                    valid_lines = []
                    for line in content.splitlines():
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if line.lower() in ("bash", "sh", "console", "terminal", "intento", "```bash", "```sh", "```"):
                            continue
                        valid_lines.append(line)
                    cmd = " && ".join(valid_lines)
                else:
                    if target_file == "main_output.js":
                        cmd = f"node {target_file}"
                    else:
                        cmd = f'"{python_exe}" {target_file}'
            else:
                cmd = f'"{python_exe}" main_output.py'

        # Intelligent Port Collision Detection and Auto-Cleanup
        ports_in_cmd = re.findall(r'\b(3000|5000|8000|8080|8001|3001)\b', cmd)
        for p_str in set(ports_in_cmd):
            p_int = int(p_str)
            for active_p in get_listening_ports():
                if active_p['port'] == p_int and active_p['pid'] != os.getpid():
                    state.launcher_logs.append(f"[SISTEMA] 🧹 Puerto {p_int} ocupado. Liberando puerto matando PID {active_p['pid']} ({active_p['name']})...")
                    try:
                        SysTools.kill_process_tree(active_p['pid'])
                        time.sleep(0.3)
                    except Exception as ex:
                        state.launcher_logs.append(f"[SISTEMA] Error al liberar puerto {p_int}: {ex}")

            free_p = SysTools.get_free_port(p_int)
            if free_p != p_int:
                cmd = re.sub(rf'\b{p_str}\b', str(free_p), cmd)
                state.launcher_logs.append(f"[SISTEMA] Puerto {p_str} sigue ocupado. Re-enrutando a puerto libre {free_p}.")

        # Determine port for environment and context
        start_port = getattr(state, "default_port", 5000)
        final_ports = re.findall(r'\b\d{4,5}\b', cmd)
        if final_ports:
            port = int(final_ports[0])
        else:
            port = SysTools.get_free_port(start_port)

        state.active_port = port
        state.launcher_logs.append(f"[SISTEMA] Puerto asignado para ejecución: {port}")

        if "5000" in cmd and str(port) != "5000":
            cmd = cmd.replace("5000", str(port))

        state.launcher_logs.append(f"[SISTEMA] Ejecutando: {cmd}")

        proc_env = os.environ.copy()
        proc_env["PORT"] = str(port)

        proc = subprocess.Popen(
            cmd, shell=True, cwd=SysTools.WORKSPACE,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            env=proc_env, text=True, bufsize=1, encoding='utf-8', errors='replace'
        )
        state.active_process = proc
        import threading
        threading.Thread(target=self_heal.stream_process_output, args=(proc, model), daemon=True).start()
        return True, f"Secuencia iniciada en puerto {port}: {cmd}"
    except Exception as e:
        return False, str(e)
