"""Multi-agent orchestrator — Phase 1 (SPEC) + Phase 2 (swarm build).

Migrated 1:1 from the legacy monolith ``run_agent_pipeline`` and
``run_agent_pipeline_phase_2``.
"""

import os
import shutil
import threading
from typing import Dict, Any

from ..core.state import state
from ..llm.provider import AIProvider
from ..tools.cache import OptTools
from ..tools.sys_tools import SysTools
from . import self_heal
from . import launcher
from ..agents.prompts import (
    architect_prompt,
    dba_prompt,
    frontend_prompt,
    backend_prompt,
    code_review_prompt,
    fix_prompt,
    ux_audit_prompt,
    qa_devops_prompt,
    style_memory_str,
)

# Wire the launch-sequence callback into self_heal (breaks the circular dep).
self_heal.set_launch_fn(launcher.run_launch_sequence)


def _get_preflight() -> Dict[str, bool]:
    """Detect which host tools are available on PATH."""
    return {
        "node": bool(shutil.which('node')),
        "docker": bool(shutil.which('docker')),
        "python": bool(shutil.which('python') or shutil.which('python3')),
        "git": bool(shutil.which('git'))
    }


def _existing_context(prompt: str) -> str:
    """Return incremental project-file context if the workspace is non-empty."""
    if os.path.exists(SysTools.WORKSPACE) and os.listdir(SysTools.WORKSPACE):
        return f"\n\nArchivos actuales del proyecto para referencia incremental:\n{OptTools.get_relevant_files_context(prompt)}"
    return ""


def run_agent_pipeline(prompt: str, model: str) -> None:
    """Phase 1 — Infra check + web search + Architect agent → SPEC.md.

    Parks the pipeline in ``waiting_spec_approval`` pending user review.
    """
    state.is_running = True
    state.pipeline_status = "running"
    state.logs = []
    SysTools.setup()

    try:
        is_gemini = model.startswith("gemini-")
        if is_gemini:
            # The legacy version raises if no Gemini key is present.
            if not os.environ.get("GEMINI_API_KEY"):
                raise Exception("GEMINI_API_KEY no configurada. Añádela a tu archivo .env o .env.local")
            target_model = model
        else:
            from ..llm.ollama import OllamaProvider
            ollama = OllamaProvider()
            if not ollama.is_available():
                raise Exception("Ollama no responde. Enciende Ollama (11434).")
            models = ollama.list_models()
            if not models:
                raise Exception("No tienes modelos descargados en Ollama. Haz 'ollama run qwen2.5-coder' en tu terminal primero.")
            target_model = model if model in models else models[0]

        state.log(f"🔎 [AGENTE INFRA]: Buscando contexto web para '{prompt}'...")
        search_ctx = SysTools.web_search(prompt + " best practices")
        state.log("✅ Contexto Web obtenido.")

        state.log(f"🧠 [AGENTE ARQUITECTO] ({target_model}): Diseñando esquema global...")

        preflight = _get_preflight()
        existing_context = _existing_context(prompt)

        arch_prompt = architect_prompt(prompt, search_ctx, preflight, existing_context)
        plan = AIProvider().generate(model=target_model, prompt=arch_prompt)
        SysTools.write("SPEC.md", plan)
        SysTools.write("ARCHITECTURE.md", plan)

        # Read the generated SPEC.md to find STACK and build manifest (SQUAD 2.0)
        stack = "FASTAPI_HTMX"
        import re
        stack_match = re.search(r'STACK:\s*([A-Z0-9_]+)', plan)
        if stack_match:
            stack = stack_match.group(1).strip()

        allowed_files = []
        if stack == "FASTAPI_HTMX":
            allowed_files = ["main_output.py", "app.py", "styles.css", "index.html", "requirements.txt"]
        elif stack == "NODE_EJS":
            allowed_files = ["server.js", "views/index.ejs", "public/styles.css", "public/app.js", "package.json"]
        elif stack == "PYTHON_STREAMLIT":
            allowed_files = ["app.py", "requirements.txt"]

        import json
        manifest_data = {
            "stack": stack,
            "files": allowed_files
        }
        SysTools.write("build_manifest.json", json.dumps(manifest_data, indent=2), force=True)

        state.log("✅ Especificación del Proyecto generada (SPEC.md).")

        # Save pipeline parameters to resume Phase 2
        state.pending_pipeline_data = {
            "prompt": prompt,
            "model": model,
            "target_model": target_model,
            "search_ctx": search_ctx,
            "plan": plan
        }
        state.pipeline_status = "waiting_spec_approval"
        state.is_running = False
        state.log("⏸️ Pipeline en pausa. Esperando revisión y aprobación de SPEC.md...")
    except Exception as e:
        state.log(f"❌ ERROR EN FASE 1: {str(e)}")
        state.is_running = False
        state.pipeline_status = "idle"


def run_agent_pipeline_phase_2() -> None:
    """Phase 2 — DBA + Frontend (parallel) → Backend → Review → UX → QA → DevOps → Git."""
    data = getattr(state, "pending_pipeline_data", {})
    if not data:
        state.log("❌ Error: No hay datos de pipeline pendientes para reanudar.")
        state.pipeline_status = "idle"
        state.is_running = False
        return

    prompt = data.get("prompt")
    model = data.get("model")
    target_model = data.get("target_model")

    plan = SysTools.read("SPEC.md")
    if not plan:
        plan = data.get("plan")

    # Parse stack from SPEC.md
    stack = "FASTAPI_HTMX"
    if plan:
        import re
        stack_match = re.search(r'STACK:\s*([A-Z0-9_]+)', plan)
        if stack_match:
            stack = stack_match.group(1).strip()
            state.log(f"📦 [SISTEMA] Stack tecnológico detectado: {stack}")
        else:
            state.log("⚠️ No se detectó STACK: en SPEC.md. Usando FASTAPI_HTMX por defecto.")

    # Cleanup conflicting workspace files of other stacks (prevent model inertia and launcher confusion)
    if stack in ["FASTAPI_HTMX", "PYTHON_STREAMLIT"]:
        for legacy_file in ["package.json", "package-lock.json", "app.js", "server.js", "webpack.config.js"]:
            p = os.path.join(SysTools.WORKSPACE, legacy_file)
            if os.path.exists(p):
                try:
                    os.remove(p)
                    state.log(f"🧹 [SISTEMA] Eliminado archivo heredado de Node/JS: {legacy_file}")
                except Exception:
                    pass
        node_modules_path = os.path.join(SysTools.WORKSPACE, "node_modules")
        if os.path.exists(node_modules_path):
            try:
                shutil.rmtree(node_modules_path)
                state.log("🧹 [SISTEMA] Eliminado directorio heredado 'node_modules'")
            except Exception:
                pass
    elif stack == "NODE_EJS":
        for legacy_file in ["main_output.py", "app.py", "requirements.txt"]:
            p = os.path.join(SysTools.WORKSPACE, legacy_file)
            if os.path.exists(p):
                try:
                    os.remove(p)
                    state.log(f"🧹 [SISTEMA] Eliminado archivo heredado de Python: {legacy_file}")
                except Exception:
                    pass



    state.pipeline_status = "running"
    state.is_running = True
    state.log("🚀 Aprobado. Reanudando enjambre (Fase 2: DBA + UI + Backend + QA)...")

    try:
        existing_context = _existing_context(prompt)

        style_mem = getattr(state, "design_identity", {})
        style_mem_s = style_memory_str(style_mem)

        state.log("⚡ [SQUAD] Lanzando Agente DBA y Agente UI Frontend en paralelo...")

        db_output = [None]
        ui_output = [None]

        def run_db_agent():
            try:
                db_p = dba_prompt(plan, existing_context)
                db_output[0] = AIProvider().generate(model=target_model, prompt=db_p)
            except Exception as e:
                db_output[0] = f"Error DBA: {e}"

        def run_ui_agent():
            try:
                ui_p = frontend_prompt(plan, existing_context, style_mem_s, stack=stack)
                ui_output[0] = AIProvider().generate(model=target_model, prompt=ui_p)
            except Exception as e:
                ui_output[0] = f"Error UI: {e}"

        t_db = threading.Thread(target=run_db_agent)
        t_ui = threading.Thread(target=run_ui_agent)

        t_db.start()
        t_ui.start()

        t_db.join()
        t_ui.join()

        # DBA Write
        if db_output[0] and not db_output[0].startswith("Error DBA"):
            SysTools.extract_and_write_multifile(db_output[0])
            state.log("✅ Modelos de DB y Seguridad previstos (Paralelo).")
        else:
            state.log(f"⚠️ DBA Agent falló o dio error: {db_output[0]}")

        # Validate UI output from thread in memory (Shift-Left, SQUAD 2.0)
        created_ui: list = []
        ui_success = False
        ui_retries = 0
        if ui_output[0] and not ui_output[0].startswith("Error UI"):
            extracted = SysTools.extract_multifile_in_memory(ui_output[0])
            all_ok = True
            err_details = []
            if not extracted:
                all_ok = False
                err_details.append("No se detectó ningún bloque @@FILE: en la respuesta")
            else:
                for filepath, content in extracted.items():
                    is_ok, err_m = SysTools.check_syntax(filepath, content)
                    if not is_ok:
                        all_ok = False
                        err_details.append(f"{filepath}: {err_m}")
            if all_ok:
                for filepath, content in extracted.items():
                    SysTools.write(filepath, content)
                created_ui = list(extracted.keys())
                ui_success = True
                state.log("✅ Sistema de Diseño Frontend/UI creado (Paralelo).")
            else:
                ui_retries = 1
                state.log(f"🔄 [SHIFT-LEFT] Error de sintaxis en UI inicial (Fase Paralela): {', '.join(err_details)}. Descartando y regenerando...")

        # Sequential UI retry loop if thread output failed
        while not ui_success and ui_retries < 3:
            ui_p = frontend_prompt(plan, existing_context, style_mem_s, stack=stack)
            if ui_retries > 0:
                ui_p += f"\n\n⚠️ REINTENTO {ui_retries}/2: La generación anterior falló la validación de sintaxis. Por favor, asegúrate de cerrar todas las llaves/paréntesis y de generar el archivo completo usando @@FILE: (no uses @@PATCH:)."
            
            ui_raw = AIProvider().generate(model=target_model, prompt=ui_p)
            extracted = SysTools.extract_multifile_in_memory(ui_raw)
            all_ok = True
            err_details = []
            if not extracted:
                all_ok = False
                err_details.append("No se detectó ningún bloque @@FILE: en la respuesta")
            else:
                for filepath, content in extracted.items():
                    is_ok, err_m = SysTools.check_syntax(filepath, content)
                    if not is_ok:
                        all_ok = False
                        err_details.append(f"{filepath}: {err_m}")
            if all_ok:
                for filepath, content in extracted.items():
                    SysTools.write(filepath, content)
                created_ui = list(extracted.keys())
                ui_success = True
                state.log("✅ Sistema de Diseño Frontend/UI creado (Fase Secuencial).")
            else:
                ui_retries += 1
                if ui_retries >= 3:
                    state.log(f"❌ [SHIFT-LEFT] UI Agent falló la validación de sintaxis 2 veces: {', '.join(err_details)}. Abortando y guardando respuesta para depuración.")
                    for filepath, content in extracted.items():
                        SysTools.write(filepath, content)
                    created_ui = list(extracted.keys())
                else:
                    state.log(f"🔄 [SHIFT-LEFT] Error de sintaxis en UI (Reintento {ui_retries}/2): {', '.join(err_details)}. Descartando y regenerando...")

        # Recalculate context so that the Backend Agent can see the newly generated schema.sql and index.html (SQUAD 2.0 Cooperability)
        existing_context = _existing_context(prompt)

        # Backend Agent execution with Shift-Left memory loop (SQUAD 2.0)
        state.log(f"💻 [AGENTE BACKEND DEV] ({target_model}): Escribiendo Lógica de Negocio y APIs...")
        created_back: list = []
        back_success = False
        back_retries = 0
        while not back_success and back_retries < 3:
            code_p = backend_prompt(plan, existing_context, stack=stack)
            if back_retries > 0:
                code_p += f"\n\n⚠️ REINTENTO {back_retries}/2: La generación anterior falló la validación de sintaxis. Por favor, regenera la lógica COMPLETAMENTE desde cero asegurándote de no dejar llaves o paréntesis abiertos y usando @@FILE: (no uses @@PATCH:)."
            
            back_raw = AIProvider().generate(model=target_model, prompt=code_p)
            extracted = SysTools.extract_multifile_in_memory(back_raw)
            all_ok = True
            err_details = []
            if not extracted:
                all_ok = False
                err_details.append("No se detectó ningún bloque @@FILE: en la respuesta")
            else:
                for filepath, content in extracted.items():
                    is_ok, err_m = SysTools.check_syntax(filepath, content)
                    if not is_ok:
                        all_ok = False
                        err_details.append(f"{filepath}: {err_m}")
            if all_ok:
                for filepath, content in extracted.items():
                    SysTools.write(filepath, content)
                created_back = list(extracted.keys())
                back_success = True
                state.log("✅ Lógica de Negocio Backend creada con éxito.")
            else:
                back_retries += 1
                if back_retries >= 3:
                    state.log(f"❌ [SHIFT-LEFT] Backend Agent falló la validación de sintaxis 2 veces: {', '.join(err_details)}. Abortando y guardando respuesta para depuración.")
                    for filepath, content in extracted.items():
                        SysTools.write(filepath, content)
                    created_back = list(extracted.keys())
                else:
                    state.log(f"🔄 [SHIFT-LEFT] Error de sintaxis en Backend (Reintento {back_retries}/2): {', '.join(err_details)}. Descartando y regenerando...")

        created_files = list(set(created_ui + created_back))
        state.log(f"✅ Se crearon/modificaron {len(created_files)} archivos en total...")

        state.log(f"🤖 [AGENTE CODE REVIEWER] ({target_model}): Analizando calidad de código generado...")
        review_p = code_review_prompt(plan, created_files)
        code_review = AIProvider().generate(model=target_model, prompt=review_p)

        if "SÍ_CRITICO" in code_review.upper():
            state.log("⚠️ El Code Reviewer detectó fallos. Inyectando AGENTE LINTER AUTÓNOMO...")
            fix_p = fix_prompt(code_review)
            fix_out = AIProvider().generate(model=target_model, prompt=fix_p)
            SysTools.extract_and_write_multifile(fix_out)
            state.log("🧹 Linter Autónomo resolvió los bugs del Review.")
        else:
            state.log("✅ Code Review superado con excelencia (Clean Code).")

        # Multi-language linter validation
        state.log("🧹 [SYNTAX CHECK]: Verificando sintaxis de archivos creados...")
        syntax_errors: list = []
        for cf in created_files:
            full_path = os.path.join(SysTools.WORKSPACE, cf)
            if os.path.exists(full_path):
                ok, linter_msg = SysTools.run_linter(full_path)
                if not ok:
                    syntax_errors.append(f"Archivo: {cf}\nError: {linter_msg}")
                    state.log(f"⚠️ Error de Sintaxis en {cf}: {linter_msg}")

        if syntax_errors:
            state.log("🧹 [LINTER AUTÓNOMO]: Corrigiendo errores de sintaxis detectados...")
            self_heal.run_autonomous_linter(syntax_errors, target_model)
            state.log("✅ Errores de sintaxis reparados.")

        # UI/UX Visual Linter Audit
        state.log("🎨 [AGENTE AUDITOR UX]: Ejecutando auditoría de calidad visual...")
        try:
            index_html = SysTools.read("index.html")
            styles_css = SysTools.read("styles.css")
            ux_audit_prompt_text = ux_audit_prompt(index_html, styles_css)
            ux_report = AIProvider().generate(model=target_model, prompt=ux_audit_prompt_text)
            SysTools.write("VISUAL_REPORT.md", ux_report)
            state.log("🎨 [AGENTE AUDITOR UX]: Reporte de diseño generado en VISUAL_REPORT.md")
        except Exception as e:
            state.log(f"⚠️ No se pudo autogenerar el reporte de calidad visual: {e}")

        state.log(f"🧪 [AGENTE QA & DEVOPS] ({target_model}): Scripts de Testing y Pipeline CI/CD...")
        qa_p = qa_devops_prompt()
        test_out = AIProvider().generate(model=target_model, prompt=qa_p)
        SysTools.extract_and_write_multifile(test_out)
        state.log("✅ Suite QA y pipelines de DevOps finalizados.")

        state.log("⏱️ [SHADOW GIT]: Documentando snapshot del Workspace...")
        git_ok, git_msg = SysTools.git_init_and_commit("Auto-commit: Workspace AI V7 Multi-Agent")
        state.log(f"✅ {git_msg}")

        state.log("\n🏆 SQUAD SYSTEM: Motor Multi-Agente ORCHESTRATOR Finalizado.")
    except Exception as e:
        state.log(f"❌ ERROR CRÍTICO DEL ENJAMBRE: {str(e)}")
    finally:
        state.is_running = False
        state.pipeline_status = "idle"
