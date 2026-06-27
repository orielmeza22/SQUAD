"""Autonomous self-healing linter and runtime watchdog.

Migrated 1:1 from the legacy monolith ``run_autonomous_linter`` and
``stream_process_output``.
"""

import os
import re
import threading
from typing import List, Optional

from ..core.state import state
from ..llm.provider import AIProvider
from ..tools.cache import OptTools
from ..tools.sys_tools import SysTools

# Forward reference — set after module creation to avoid circular imports
_run_launch_sequence = None  # type: ignore


def set_launch_fn(fn):
    """Wire the launch-sequence callback (set by the orchestrator module)."""
    global _run_launch_sequence
    _run_launch_sequence = fn


def run_autonomous_linter(error_logs_list: List[str], model: str):
    """Feed error logs + all workspace files to the LLM and apply @@FILE/@@PATCH fixes.

    Temporarily disables critical-file interception so the fixes go through.
    """
    state.launcher_logs.append("🧹 [LINTER AUTÓNOMO]: Iniciando diagnóstico de código...")
    error_summary = "\n".join(error_logs_list)

    files_context: list = []
    if os.path.exists(SysTools.WORKSPACE):
        for root, _, files in os.walk(SysTools.WORKSPACE):
            if any(skip in root for skip in (".git", "node_modules", "__pycache__", "venv")):
                continue
            for f in files:
                rel = os.path.relpath(os.path.join(root, f), SysTools.WORKSPACE).replace('\\', '/')
                # Use in-memory broken version if it exists, otherwise read from disk
                content = SysTools.broken_memory_files.get(rel) or SysTools.read(rel)
                files_context.append(f"@@FILE: {rel}\n{content}\n@@ENDFILE@@")

    # Add any in-memory broken files that do not exist on disk yet
    for rel, content in SysTools.broken_memory_files.items():
        if not any(f.startswith(f"@@FILE: {rel}\n") for f in files_context):
            files_context.append(f"@@FILE: {rel}\n{content}\n@@ENDFILE@@")

    files_context_str = "\n\n".join(files_context)

    prompt = (
        "Eres el Agente Linter de Emergencia de SQUAD. La aplicación local acaba de crashear "
        "durante la ejecución.\n"
        "A continuación se muestran los logs de error de la terminal:\n"
        "---\n"
        f"{error_summary}\n"
        "---\n\n"
        "Los archivos actuales en el espacio de trabajo son:\n"
        "---\n"
        f"{files_context_str}\n"
        "---\n\n"
        "Tu objetivo es solucionar el error. Puede ser una importación faltante, un error de "
        "sintaxis, dependencias desalineadas, etc.\n"
        "REGLA DE IMPORTACIÓN: Si el error se debe a una importación local de un archivo inexistente "
        "(como require('./config')), debes reescribir el archivo importador para incorporar esa "
        "lógica directamente (autocontenido) o generar el archivo faltante con la sintaxis "
        "@@FILE: en tu respuesta.\n"
        "REGLA DE PUERTO: El servidor siempre debe escuchar en el puerto definido por la variable "
        "de entorno PORT (process.env.PORT o os.environ.get('PORT')), utilizando un fallback "
        "adecuado si no está definida.\n"
        f"{OptTools.CODE_GUIDELINES}\n\n"
        "REGLA DE FORMATO OBLIGATORIA (REGENERACIÓN COMPLETA): Debes responder ÚNICAMENTE utilizando el siguiente "
        "formato para cada archivo que modifiques o crees. No utilices parches parciales, escribe siempre el archivo completo:\n\n"
        "@@FILE: nombre_del_archivo\ncódigo completo aquí\n@@ENDFILE@@\n\n"
        "No agregues ninguna explicación ni texto introductorio ni conclusiones. Solo genera "
        "las correcciones de archivos con el formato indicado."
    )

    try:
        orig_val = getattr(state, "interception_enabled", True)
        state.interception_enabled = False
        fixed_output = AIProvider().generate(model=model, prompt=prompt, no_cache=True)
        corrected_files = SysTools.extract_and_write_multifile(fixed_output)
        state.launcher_logs.append(
            f"🧹 [LINTER AUTÓNOMO]: Reparación aplicada sobre archivos: {str(corrected_files)}"
        )
    except Exception as e:
        state.launcher_logs.append(f"❌ [LINTER AUTÓNOMO] Error invocando IA para reparación: {e}")
    finally:
        state.interception_enabled = orig_val


def stream_process_output(proc, model: str):
    """Read launched-process stdout, detect crashes, trigger autonomous linter + relaunch.

    Parses Python/JS tracebacks, sets ``state.active_diagnostic``, and retries
    up to 3 times.
    """
    has_crashed = False
    error_lines: list = []

    proc.last_err_loc = None  # type: ignore[attr-defined]

    while True:
        line = proc.stdout.readline()
        if not line and proc.poll() is not None:
            break
        if line:
            line_str = line.decode('utf-8', errors='ignore').strip() if isinstance(line, bytes) else line.strip()
            state.launcher_logs.append(line_str)
            print(f"[LAUNCHER] {line_str}")

            # Python traceback parser
            py_match = re.search(r'File "([^"]+)", line (\d+)', line_str)
            if py_match:
                proc.last_err_loc = (py_match.group(1), py_match.group(2))  # type: ignore[attr-defined]

            if any(marker in line_str for marker in [
                "ModuleNotFoundError:", "NameError:", "TypeError:",
                "ValueError:", "SyntaxError:"
            ]):
                has_crashed = True
                loc = getattr(proc, "last_err_loc", None) or ("app.py", "1")
                state.active_diagnostic = {
                    "error": line_str,
                    "file": loc[0],
                    "line": loc[1],
                    "suggestion": "Se detectó una excepción de Python. Usa 'Auto-reparar con IA' o edita el archivo en Monaco."
                }
                print(f"[LAUNCHER] ⚠️ Error fatal detectado ({line_str}). Forzando reinicio para auto-reparación.")
                try:
                    SysTools.kill_process_tree(proc.pid)
                except Exception:
                    pass
            elif any(marker in line_str for marker in ["ReferenceError:", "TypeError:", "SyntaxError:"]):
                has_crashed = True
                js_match = re.search(r'([a-zA-Z0-9_\-\.]+):(\d+)', line_str)
                if js_match:
                    state.active_diagnostic = {
                        "error": line_str,
                        "file": js_match.group(1),
                        "line": js_match.group(2),
                        "suggestion": "Se detectó un error en el código JS. Revisa la línea señalada en Monaco."
                    }
                else:
                    state.active_diagnostic = {
                        "error": line_str,
                        "file": "unknown",
                        "line": "1",
                        "suggestion": "Se detectó un error en JS. Revisa los logs de consola."
                    }
            elif any(marker in line_str for marker in ["Error:", "Traceback (most recent call last):"]):
                has_crashed = True

            if has_crashed or any(marker in line_str.lower() for marker in ["fail", "error", "exception"]):
                error_lines.append(line_str)
                if len(error_lines) > 30:
                    error_lines.pop(0)

    ret_code = proc.poll()
    if (ret_code is not None and ret_code != 0) or has_crashed:
        state.launcher_logs.append("[LINTER AUTÓNOMO] 🧹 Detectado crash o error de ejecución.")
        if state.linter_retries < 3:
            state.linter_retries += 1
            state.launcher_logs.append(
                f"[LINTER AUTÓNOMO] 🔄 Intento de autoreparación {state.linter_retries}/3 en progreso..."
            )
            try:
                run_autonomous_linter(error_lines, model)
                state.launcher_logs.append("[LINTER AUTÓNOMO] 🚀 Lanzando de nuevo tras reparación...")
                if _run_launch_sequence:
                    threading.Thread(target=_run_launch_sequence, args=(model,), daemon=True).start()
            except Exception as e:
                state.launcher_logs.append(f"❌ [LINTER AUTÓNOMO] Error en ciclo de reparación: {e}")
        else:
            state.launcher_logs.append("⚠️ [LINTER AUTÓNOMO] Límite de autoreparación alcanzado. Por favor corrige manualmente en el Monaco Editor.")
