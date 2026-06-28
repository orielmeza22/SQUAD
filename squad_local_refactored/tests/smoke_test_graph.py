"""End-to-end smoke test for the LangGraph orchestrator.

Corre el grafo completo con una app TODO simple, simula la aprobación
de SPEC, verifica que los archivos se generan, arranca la app y
verifica que responde. Requiere GEMINI_API_KEY o un Ollama corriendo.
"""
import os
import sys
import time
import json
import shutil
import requests
import argparse
from pathlib import Path

# Reconfigure stdout/stderr to UTF-8 to handle emojis safely on Windows
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    pass

# Add project root to path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "squad_local_refactored"))

from src.core.state import state
from src.core.config import settings as pydantic_settings
from src.core.settings_loader import load_settings
from src.tools.sys_tools import SysTools


def _await(condition, timeout=120, interval=1.0, label=""):
    """Espera hasta que condition() sea True o timeout."""
    start = time.time()
    while time.time() - start < timeout:
        if condition():
            return True
        time.sleep(interval)
    raise TimeoutError(f"Timeout esperando: {label}")


def main(model: str = "gemini-2.5-flash", keep: bool = False):
    print("=" * 70)
    print(" SMOKE TEST END-TO-END: LangGraph Orchestrator")
    print("=" * 70)

    report = {"steps": [], "failures": [], "success": False}

    def step(name, ok, detail=""):
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"  {status}  {name}  {detail}")
        report["steps"].append({"name": name, "ok": ok, "detail": detail})
        if not ok:
            report["failures"].append(name)

    # --- 1. Setup ---
    load_settings()
    pydantic_settings.orchestrator_mode = "graph"
    test_workspace = ROOT / "smoke_test_workspace"
    if test_workspace.exists():
        shutil.rmtree(test_workspace)
    test_workspace.mkdir()
    SysTools.WORKSPACE = str(test_workspace)
    state.pipeline_status = "idle"
    state.is_running = False
    state.logs.clear()
    state.graph_run_id = None
    state.pending_writes = {}
    state.graph_node_status.clear()
    state.graph_last_error = None

    try:
        # --- 2. Lanzar Fase 1 (architect) ---
        from src.pipeline.graph_orchestrator import run_graph_pipeline
        run_id = run_graph_pipeline(
            prompt="Hazme una app de lista de tareas (TODO) en FastAPI con SQLite. Endpoints GET y POST en /.",
            model=model
        )
        step("1. Pipeline lanzado", bool(run_id), f"run_id={run_id}")
        report["run_id"] = run_id

        # --- 3. Esperar pausa SPEC ---
        _await(lambda: state.pipeline_status == "waiting_spec_approval",
               timeout=180, label="SPEC approval pause")
        spec_path = test_workspace / "SPEC.md"
        step("2. SPEC.md generado", spec_path.exists(), f"{len(spec_path.read_text()) if spec_path.exists() else 0} bytes")
        step("3. Pipeline pausado en SPEC", state.pipeline_status == "waiting_spec_approval")

        # --- 4. Aprobar y reanudar ---
        from src.pipeline.graph_orchestrator import resume_after_spec_approval
        resume_after_spec_approval(run_id)
        _await(lambda: state.pipeline_status != "waiting_spec_approval",
               timeout=180, label="SPEC resume")

        # --- 5. Esperar finalización ---
        _await(lambda: state.pipeline_status in ("idle", "waiting_hitl_approval"),
               timeout=300, label="graph completion")

        # --- 6. Verificar archivos ---
        expected_files = ["SPEC.md", "build_manifest.json", "main_output.py", "index.html", "requirements.txt"]
        for f in expected_files:
            exists = (test_workspace / f).exists()
            step(f"4. Archivo generado: {f}", exists)

        # --- 7. Intentar arrancar la app ---
        main_file = test_workspace / "main_output.py"
        if main_file.exists():
            try:
                import subprocess
                # Instalar deps
                req_path = test_workspace / "requirements.txt"
                if req_path.exists():
                    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", str(req_path)],
                                   capture_output=True, timeout=120)
                # Arrancar app
                proc = subprocess.Popen(
                    [sys.executable, str(main_file)],
                    cwd=str(test_workspace),
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    env={**os.environ, "PORT": "8799"}
                )
                time.sleep(8)
                try:
                    resp = requests.get("http://127.0.0.1:8799/", timeout=10)
                    step("5. App responde 200", resp.status_code == 200, f"status={resp.status_code}")
                except Exception as e:
                    step("5. App responde 200", False, str(e))
                finally:
                    proc.terminate()
                    try: proc.wait(timeout=5)
                    except Exception: proc.kill()
            except Exception as e:
                step("5. App arranca", False, str(e))
        else:
            step("5. App arranca", False, "main_output.py no existe")

        # --- 8. Reporte de errores del grafo ---
        if state.graph_last_error:
            step("6. Sin errores críticos del grafo", False, state.graph_last_error[:100])
        else:
            step("6. Sin errores críticos del grafo", True)

    except Exception as e:
        step("Sin excepciones en el flujo", False, str(e))
        import traceback
        report["traceback"] = traceback.format_exc()
    finally:
        report["success"] = len(report["failures"]) == 0
        print("\n" + "=" * 70)
        print(f" RESULTADO: {'✅ TODO OK' if report['success'] else '❌ HAY FALLOS'}")
        print("=" * 70)

        # Guardar reporte
        report_path = ROOT / "SMOKE_TEST_REPORT.md"
        with open(report_path, "w", encoding="utf-8") as SMOKE:
            SMOKE.write("# Smoke Test Report — LangGraph Orchestrator\n\n")
            SMOKE.write(f"**Resultado:** {'✅ PASS' if report['success'] else '❌ FAIL'}\n\n")
            SMOKE.write(f"**Fecha:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            SMOKE.write(f"**Run ID:** {report.get('run_id', 'N/A')}\n\n")
            SMOKE.write("## Pasos\n\n")
            for s in report["steps"]:
                icon = "✅" if s["ok"] else "❌"
                SMOKE.write(f"- {icon} **{s['name']}**: {s['detail']}\n")
            if report.get("traceback"):
                SMOKE.write("\n## Traceback\n\n```\n" + report["traceback"] + "\n```\n")
        print(f"📄 Reporte guardado en: {report_path}")

        # Limpieza
        if not keep and report["success"]:
            shutil.rmtree(test_workspace, ignore_errors=True)
            print(f"🧹 Workspace temporal eliminado.")

    return report["success"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="gemini-2.5-flash")
    parser.add_argument("--keep", action="store_true", help="Conservar workspace temporal")
    args = parser.parse_args()
    success = main(model=args.model, keep=args.keep)
    sys.exit(0 if success else 1)
