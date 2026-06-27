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

        created_ui: list = []
        if db_output[0] and not db_output[0].startswith("Error DBA"):
            SysTools.extract_and_write_multifile(db_output[0])
            state.log("✅ Modelos de DB y Seguridad previstos (Paralelo).")
        else:
            state.log(f"⚠️ DBA Agent falló o dio error: {db_output[0]}")

        if ui_output[0] and not ui_output[0].startswith("Error UI"):
            created_ui = SysTools.extract_and_write_multifile(ui_output[0])
            state.log("✅ Sistema de Diseño Frontend/UI creado (Paralelo).")
        else:
            state.log(f"⚠️ UI Agent falló o dio error: {ui_output[0]}")

        state.log(f"💻 [AGENTE BACKEND DEV] ({target_model}): Escribiendo Lógica de Negocio y APIs...")
        code_p = backend_prompt(plan, existing_context, stack=stack)
        full_code_output = AIProvider().generate(model=target_model, prompt=code_p)
        created_back = SysTools.extract_and_write_multifile(full_code_output)

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
