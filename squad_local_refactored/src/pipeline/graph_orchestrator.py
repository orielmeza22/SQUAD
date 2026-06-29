"""LangGraph-based orchestrator with graceful fallback to legacy pipeline."""
import os
import shutil
import re
import json
import uuid
from typing import TypedDict, List, Dict, Any, Optional, Tuple

from ..core.state import state
from ..core.config import settings
from ..llm.provider import AIProvider
from ..tools.cache import OptTools
from ..tools.sys_tools import SysTools
from . import self_heal

try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.sqlite import SqliteSaver
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    StateGraph = None  # type: ignore
    SqliteSaver = None  # type: ignore

def is_graph_mode_available() -> bool:
    return LANGGRAPH_AVAILABLE

class SquadGraphState(TypedDict):
    prompt: str
    model: str
    target_model: str
    search_ctx: str
    plan: str                     # SPEC.md content
    stack: str
    created_files: List[str]
    last_errors: List[str]        # errores acumulados para reinyectar
    review_verdict: str           # "PASS" | "FAIL"
    retries: Dict[str, int]       # {agent_name: retry_count}
    messages: List[str]           # log interno del grafo


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

def _get_created_files(stack: str) -> List[str]:
    manifest_path = os.path.join(SysTools.WORKSPACE, "build_manifest.json")
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            files = data.get("files", [])
            existing = []
            for f in files:
                if os.path.exists(os.path.join(SysTools.WORKSPACE, f)):
                    existing.append(f)
            return existing
        except Exception:
            pass
    return []

# NODES DEFINITIONS

def node_architect(state_val: SquadGraphState) -> dict:
    state.set_node_status("architect", "executing")
    prompt = state_val["prompt"]
    target_model = state_val["target_model"]
    
    state.log(f"🔎 [AGENTE INFRA]: Buscando contexto web para '{prompt}'...")
    search_ctx = SysTools.web_search(prompt + " best practices")
    state.log("✅ Contexto Web obtenido.")

    state.log(f"🧠 [AGENTE ARQUITECTO] ({target_model}): Diseñando esquema global...")
    preflight = _get_preflight()
    existing_context = _existing_context(prompt)

    from ..agents.prompts import architect_prompt
    arch_prompt = architect_prompt(prompt, search_ctx, preflight, existing_context)
    plan = AIProvider().generate(model=target_model, prompt=arch_prompt)
    
    SysTools.write("SPEC.md", plan)
    SysTools.write("ARCHITECTURE.md", plan)
    
    stack = "FASTAPI_HTMX"
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

    manifest_data = {
        "stack": stack,
        "files": allowed_files
    }
    SysTools.write("build_manifest.json", json.dumps(manifest_data, indent=2), force=True)
    
    # RAG: Index SPEC.md if enabled
    from ..core.config import settings
    if getattr(settings, "rag_enabled", False):
        try:
            from ..tools.rag_indexer import RAGIndexer
            indexer = RAGIndexer(SysTools.WORKSPACE, getattr(settings, "rag_collection_name", "squad_workspace"))
            indexer.index_file("SPEC.md", plan, "markdown")
            state.log("🔍 [RAG]: SPEC.md indexado en base vectorial.")
        except Exception as e:
            state.log(f"⚠️ Error indexing SPEC.md: {e}")

    state.log("✅ Especificación del Proyecto generada (SPEC.md).")
    
    state.set_node_status("architect", "done")
    return {
        "search_ctx": search_ctx,
        "plan": plan,
        "stack": stack,
        "messages": state_val["messages"] + ["Architect completed spec generation."]
    }

def node_dba(state_val: SquadGraphState) -> dict:
    state.set_node_status("dba", "executing")
    plan = SysTools.read("SPEC.md") or state_val["plan"]
    prompt = state_val["prompt"]
    target_model = state_val["target_model"]
    stack = state_val["stack"]

    # Workspace cleanups
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

    existing_context = _existing_context(prompt)
    from ..agents.prompts import dba_prompt
    db_p = dba_prompt(plan, existing_context)
    db_output = AIProvider().generate(model=target_model, prompt=db_p)

    if db_output and not db_output.startswith("Error DBA"):
        from ..tools.action_executor import ActionExecutor
        ActionExecutor().execute_all(db_output)
        state.log("✅ Modelos de DB y Seguridad previstos (Paralelo).")
    else:
        state.log(f"⚠️ DBA Agent falló o dio error: {db_output}")

    state.set_node_status("dba", "done")
    return {
        "messages": state_val["messages"] + ["DBA completed schema generation."]
    }

def node_frontend(state_val: SquadGraphState) -> dict:
    state.set_node_status("frontend", "executing")
    retries = state_val["retries"].copy()
    retries["frontend"] = retries.get("frontend", 0) + 1
    
    plan = SysTools.read("SPEC.md") or state_val["plan"]
    prompt = state_val["prompt"]
    target_model = state_val["target_model"]
    stack = state_val["stack"]
    
    existing_context = _existing_context(prompt)
    style_mem = getattr(state, "design_identity", {})
    from ..agents.prompts import style_memory_str, frontend_prompt
    style_mem_s = style_memory_str(style_mem)

    # RAG enrichment
    from ..tools.context_enricher import enrich_context
    rag_ctx = enrich_context("frontend", plan)
    ui_p = frontend_prompt(plan, existing_context, style_mem_s, stack=stack)
    if rag_ctx:
        ui_p += "\n\n" + rag_ctx

    if retries["frontend"] > 1 and state_val["last_errors"]:
        ui_p += f"\n\n⚠️ REINTENTO {retries['frontend']}/{settings.graph_max_retries}: El intento anterior falló por: {state_val['last_errors'][-1]}.\nCorrige específicamente ese error. NO regeneres todo desde cero; aplica el fix puntual."

    ui_raw = AIProvider().generate(model=target_model, prompt=ui_p)
    from ..tools.action_executor import ActionExecutor
    ActionExecutor().execute_all(ui_raw)

    # RAG workspace re-indexing
    if getattr(settings, "rag_enabled", False):
        try:
            from ..tools.rag_indexer import RAGIndexer
            RAGIndexer(SysTools.WORKSPACE, getattr(settings, "rag_collection_name", "squad_workspace")).index_workspace()
            state.log("🔍 [RAG]: Workspace re-indexado tras Frontend.")
        except Exception as e:
            state.log(f"⚠️ Error re-indexing workspace: {e}")

    state.log("✅ Sistema de Diseño Frontend/UI creado.")

    state.set_node_status("frontend", "done")
    return {
        "retries": retries,
        "messages": state_val["messages"] + ["Frontend completed UI generation."]
    }

def node_backend(state_val: SquadGraphState) -> dict:
    state.set_node_status("backend", "executing")
    retries = state_val["retries"].copy()
    retries["backend"] = retries.get("backend", 0) + 1

    plan = SysTools.read("SPEC.md") or state_val["plan"]
    prompt = state_val["prompt"]
    target_model = state_val["target_model"]
    stack = state_val["stack"]

    existing_context = _existing_context(prompt)
    from ..agents.prompts import backend_prompt
    
    # RAG enrichment
    from ..tools.context_enricher import enrich_context
    rag_ctx = enrich_context("backend", plan)
    code_p = backend_prompt(plan, existing_context, stack=stack)
    if rag_ctx:
        code_p += "\n\n" + rag_ctx

    if retries["backend"] > 1 and state_val["last_errors"]:
        code_p += f"\n\n⚠️ REINTENTO {retries['backend']}/{settings.graph_max_retries}: El intento anterior falló por: {state_val['last_errors'][-1]}.\nCorrige específicamente ese error. NO regeneres todo desde cero; aplica el fix puntual."

    state.log(f"💻 [AGENTE BACKEND DEV] ({target_model}): Escribiendo Lógica de Negocio y APIs...")
    back_raw = AIProvider().generate(model=target_model, prompt=code_p)
    from ..tools.action_executor import ActionExecutor
    ActionExecutor().execute_all(back_raw)
    
    # RAG workspace re-indexing
    if getattr(settings, "rag_enabled", False):
        try:
            from ..tools.rag_indexer import RAGIndexer
            RAGIndexer(SysTools.WORKSPACE, getattr(settings, "rag_collection_name", "squad_workspace")).index_workspace()
            state.log("🔍 [RAG]: Workspace re-indexado tras Backend.")
        except Exception as e:
            state.log(f"⚠️ Error re-indexing workspace: {e}")

    state.log("✅ Lógica de Negocio Backend creada con éxito.")

    created_files = _get_created_files(stack)

    state.set_node_status("backend", "done")
    return {
        "retries": retries,
        "created_files": created_files,
        "messages": state_val["messages"] + ["Backend completed business logic."]
    }

def node_review(state_val: SquadGraphState) -> dict:
    state.set_node_status("review", "executing")
    plan = SysTools.read("SPEC.md") or state_val["plan"]
    target_model = state_val["target_model"]
    created_files = state_val["created_files"]

    state.log(f"🤖 [AGENTE CODE REVIEWER] ({target_model}): Analizando calidad de código generado...")
    
    # RAG Judge comparison
    rag_context = ""
    if getattr(settings, "rag_enabled", False):
        try:
            from ..tools.rag_indexer import RAGIndexer
            indexer = RAGIndexer(SysTools.WORKSPACE, getattr(settings, "rag_collection_name", "squad_workspace"))
            spec_queries = plan[:500].split('\n')[:5]
            results = []
            for q in spec_queries:
                if q.strip():
                    results.extend(indexer.query(q, n_results=2))
            if results:
                seen_res = set()
                uniq_res = []
                for r in results:
                    key = (r["source"], r["start_line"])
                    if key not in seen_res:
                        seen_res.add(key)
                        uniq_res.append(r)
                rag_context = "## FRAGMENTOS DE CÓDIGO vs SPEC (RAG Judge)\n\n"
                for r in uniq_res[:5]:
                    rag_context += f"**{r['source']}** (sim: {1 - r['distance']:.2f}):\n{r['document'][:500]}\n\n"
        except Exception as e:
            state.log(f"⚠️ Error in RAG Judge: {e}")

    from ..agents.prompts import code_review_prompt
    review_p = code_review_prompt(plan, created_files)
    if rag_context:
        review_p += "\n\n" + rag_context

    code_review = AIProvider().generate(model=target_model, prompt=review_p)

    verdict = "PASS"
    last_errors = state_val["last_errors"].copy()
    if "SÍ_CRITICO" in code_review.upper():
        verdict = "FAIL"
        last_errors.append(code_review)
        state.graph_last_error = code_review
        state.log("⚠️ El Code Reviewer detectó fallos.")
    else:
        state.log("✅ Code Review superado con excelencia (Clean Code).")

    state.set_node_status("review", "done")
    return {
        "review_verdict": verdict,
        "last_errors": last_errors,
        "messages": state_val["messages"] + [f"Review verdict: {verdict}"]
    }

def _is_destructive_action(cmd: str) -> bool:
    """Detecta si un comando requiere HITL antes de ejecutarse."""
    from ..tools.security import SecurityScanner
    findings = SecurityScanner.scan_command(cmd) if hasattr(SecurityScanner, "scan_command") else []
    if not findings:
        for pattern, _ in SecurityScanner.DANGEROUS_SHELL_PATTERNS:
            if re.search(pattern, cmd):
                return True
    return len(findings) > 0

def node_fix(state_val: SquadGraphState) -> dict:
    state.set_node_status("fix", "executing")
    retries = state_val["retries"].copy()
    retries["fix"] = retries.get("fix", 0) + 1

    target_model = state_val["target_model"]
    last_errors = state_val["last_errors"]

    if last_errors:
        state.log("⚠️ Inyectando AGENTE LINTER AUTÓNOMO para aplicar correcciones...")
        from ..agents.prompts import fix_prompt
        fix_p = fix_prompt(last_errors[-1])
        
        # RAG enrichment
        from ..tools.context_enricher import enrich_context
        rag_ctx = enrich_context("fix", last_errors[-1])
        if rag_ctx:
            fix_p += "\n\n" + rag_ctx

        fix_out = AIProvider().generate(model=target_model, prompt=fix_p)
        
        # HITL: verificar acciones destructivas antes de ejecutar
        from ..tools.action_executor import ActionExecutor
        executor = ActionExecutor()
        calls = executor.parse(fix_out)
        destructive = []
        for call in calls:
            if call.tool == "execute_cmd":
                cmd = call.parameters.get("cmd", "")
                if _is_destructive_action(cmd):
                    destructive.append(cmd)
        
        if destructive:
            state.log(f"⏸️ [HITL] Acción destructiva detectada: {destructive}. Pausando grafo...")
            state.pending_writes["hitl_pending_cmd"] = "\n".join(destructive)
            state.pipeline_status = "waiting_hitl_approval"
            state.set_node_status("fix", "paused_hitl")
            return {
                "retries": retries,
                "messages": state_val["messages"] + [f"HITL paused for: {destructive}"]
            }
            
        executor.execute_all(fix_out)
        
        # RAG workspace re-indexing
        if getattr(settings, "rag_enabled", False):
            try:
                from ..tools.rag_indexer import RAGIndexer
                RAGIndexer(SysTools.WORKSPACE, getattr(settings, "rag_collection_name", "squad_workspace")).index_workspace()
                state.log("🔍 [RAG]: Workspace re-indexado tras Fix.")
            except Exception as e:
                state.log(f"⚠️ Error re-indexing workspace: {e}")

        state.log("🧹 Linter Autónomo resolvió los bugs del Review.")

    state.set_node_status("fix", "done")
    return {
        "retries": retries,
        "messages": state_val["messages"] + ["Autonomous fix executed."]
    }

def node_qa(state_val: SquadGraphState) -> dict:
    state.set_node_status("qa", "executing")
    created_files = state_val["created_files"]
    target_model = state_val["target_model"]
    stack = state_val["stack"]

    # 1. Verify syntax check
    state.log("🧹 [SYNTAX CHECK]: Verificando sintaxis de archivos creados...")
    syntax_errors = []
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

    # 2. QA generation
    state.log(f"🧪 [AGENTE QA & DEVOPS] ({target_model}): Scripts de Testing y Pipeline CI/CD...")
    from ..agents.prompts import qa_devops_prompt
    qa_p = qa_devops_prompt()
    
    # RAG enrichment
    from ..tools.context_enricher import enrich_context
    plan = SysTools.read("SPEC.md") or state_val["plan"]
    rag_ctx = enrich_context("qa", plan)
    if rag_ctx:
        qa_p += "\n\n" + rag_ctx

    test_out = AIProvider().generate(model=target_model, prompt=qa_p)
    from ..tools.action_executor import ActionExecutor
    ActionExecutor().execute_all(test_out)
    state.log("✅ Suite QA y pipelines de DevOps finalizados.")

    # 3. Test execution
    last_errors = []
    test_ran = False
    if stack == "NODE_EJS":
        if os.path.exists(os.path.join(SysTools.WORKSPACE, "package.json")):
            test_ran = True
            rc, stdout, stderr = SysTools.run_command(["npm", "test"])
            if rc != 0:
                last_errors.append(f"Pruebas Node fallaron (Código {rc}): {stdout} {stderr}")
    else:
        test_files = [f for f in os.listdir(SysTools.WORKSPACE) if f.startswith("test_") and f.endswith(".py")]
        if test_files:
            test_ran = True
            rc, stdout, stderr = SysTools.run_command(["python", "-m", "pytest"] + test_files)
            if rc != 0:
                last_errors.append(f"Pruebas pytest fallaron (Código {rc}): {stdout} {stderr}")

    if test_ran:
        if last_errors:
            state.graph_last_error = last_errors[-1]
            state.log(f"❌ Pruebas fallidas: {last_errors[-1]}")
        else:
            state.log("✅ Todas las pruebas pasaron con éxito.")
            state.graph_last_error = None
            state.log("⏱️ [SHADOW GIT]: Documentando snapshot del Workspace...")
            SysTools.git_init_and_commit("Auto-commit: Workspace AI LangGraph snapshot")

    state.set_node_status("qa", "done")
    return {
        "last_errors": last_errors,
        "messages": state_val["messages"] + ["QA node completed."]
    }

# EDGES ROUTING

def route_after_review(state_val: SquadGraphState) -> str:
    """Decide si continuar a QA o volver a Backend a corregir."""
    if state_val["review_verdict"] == "FAIL":
        retries = state_val["retries"].get("backend", 0)
        if retries < getattr(settings, "graph_max_retries", 3):
            return "fix_backend"
        else:
            state_val["messages"].append("⚠️ Máximo de reintentos de Backend agotado. Continuando a QA.")
            return "qa"
    return "qa"

def route_after_qa(state_val: SquadGraphState) -> str:
    """Si QA encuentra errores de runtime, vuelve a fix; si no, termina."""
    if state_val["last_errors"]:  # QA ejecutó tests y hubo fallos
        retries = state_val["retries"].get("fix", 0)
        if retries < getattr(settings, "graph_max_retries", 3):
            return "fix_qa"
    return "devops"



def _run_with_saver(fn):
    if not LANGGRAPH_AVAILABLE:
        raise RuntimeError("LangGraph no está instalado en este entorno.")
    
    db_name = getattr(settings, "graph_checkpoint_db", "squad_checkpoints.sqlite")
    os.makedirs(SysTools.WORKSPACE, exist_ok=True)
    db_path = os.path.abspath(os.path.join(SysTools.WORKSPACE, db_name))
    
    with SqliteSaver.from_conn_string(db_path) as saver:
        workflow = StateGraph(SquadGraphState)
        workflow.add_node("architect", node_architect)
        workflow.add_node("dba", node_dba)
        workflow.add_node("frontend", node_frontend)
        workflow.add_node("backend", node_backend)
        workflow.add_node("review", node_review)
        workflow.add_node("fix", node_fix)
        workflow.add_node("qa", node_qa)

        workflow.set_entry_point("architect")
        workflow.add_edge("architect", "dba")        # arquitecto → DBA
        workflow.add_edge("dba", "frontend")          # DBA → Frontend
        workflow.add_edge("frontend", "backend")      # Frontend → Backend
        workflow.add_edge("backend", "review")        # Backend → Review
        workflow.add_conditional_edges("review", route_after_review, {
            "fix_backend": "backend",
            "qa": "qa"
        })
        workflow.add_conditional_edges("qa", route_after_qa, {
            "fix_qa": "fix",
            "devops": END
        })
        workflow.add_edge("fix", "qa")
        
        app = workflow.compile(checkpointer=saver, interrupt_after=["architect", "fix"])
        return fn(app)

# PUBLIC APIS

def run_graph_pipeline(prompt: str, model: str) -> str:
    """Entry point. Returns a run_id. Raises RuntimeError si langgraph no está."""
    if not LANGGRAPH_AVAILABLE:
        raise RuntimeError("LangGraph no está instalado en este entorno.")
    
    run_id = str(uuid.uuid4())
    state.graph_run_id = run_id
    state.pipeline_status = "running"
    state.is_running = True
    state.log(f"Iniciando pipeline de LangGraph con run_id: {run_id}")
    
    SysTools.setup()
    
    is_gemini = model.startswith("gemini-")
    if is_gemini:
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

    initial_state = {
        "prompt": prompt,
        "model": model,
        "target_model": target_model,
        "search_ctx": "",
        "plan": "",
        "stack": "FASTAPI_HTMX",
        "created_files": [],
        "last_errors": [],
        "review_verdict": "PASS",
        "retries": {},
        "messages": []
    }
    
    config = {"configurable": {"thread_id": run_id}}
    
    def _execute(app):
        try:
            app.invoke(initial_state, config)
            # Check checkpoint status to determine if we are interrupted
            state_info = app.get_state(config)
            if state_info.next:
                if "dba" in state_info.next:
                    state.pipeline_status = "waiting_spec_approval"
                    state.log("⏸️ Pipeline en pausa. Esperando revisión y aprobación de SPEC.md...")
                elif "qa" in state_info.next:
                    state.pipeline_status = "waiting_hitl_approval"
                    state.log("⏸️ Pipeline en pausa (HITL). Esperando aprobación de comando destructivo...")
                else:
                    state.pipeline_status = "waiting_spec_approval"
                state.is_running = False
            else:
                state.pipeline_status = "idle"
                state.is_running = False
                state.log("🏆 SQUAD SYSTEM: Motor Multi-Agente LangGraph Finalizado.")
        except Exception as e:
            state.log(f"❌ ERROR CRÍTICO DEL ENJAMBRE (GRAFO): {str(e)}")
            state.is_running = False
            state.pipeline_status = "idle"
            raise

    _run_with_saver(_execute)
    return run_id

def resume_graph_pipeline(run_id: str) -> bool:
    if not LANGGRAPH_AVAILABLE:
        return False
    
    # VERIFICACIÓN TEMPRANA: ¿existe el archivo de checkpoint?
    db_name = getattr(settings, "graph_checkpoint_db", "squad_checkpoints.sqlite")
    db_path = os.path.abspath(os.path.join(SysTools.WORKSPACE, db_name))
    if not os.path.exists(db_path):
        state.log(f"❌ No existe checkpoint DB en {db_path}")
        return False
    
    state.pipeline_status = "running"
    state.is_running = True
    state.graph_run_id = run_id
    state.log(f"Reanudando pipeline de LangGraph para run_id: {run_id}")
    
    config = {"configurable": {"thread_id": run_id}}
    
    def _resume(app):
        try:
            state_info = app.get_state(config)
            if not state_info or not state_info.values:
                state.log(f"❌ Checkpoint vacío o no encontrado para run_id: {run_id}")
                return False
                
            app.invoke(None, config)
            
            state_info = app.get_state(config)
            if state_info.next:
                if "dba" in state_info.next:
                    state.pipeline_status = "waiting_spec_approval"
                elif "qa" in state_info.next:
                    state.pipeline_status = "waiting_hitl_approval"
                else:
                    state.pipeline_status = "waiting_spec_approval"
                state.is_running = False
            else:
                state.pipeline_status = "idle"
                state.is_running = False
                state.log("🏆 SQUAD SYSTEM: Motor Multi-Agente LangGraph Finalizado.")
            return True
        except Exception as e:
            state.log(f"❌ ERROR CRÍTICO AL REANUDAR EL ENJAMBRE: {str(e)}")
            state.is_running = False
            state.pipeline_status = "idle"
            return False

    return _run_with_saver(_resume)

def resume_after_spec_approval(run_id: str) -> bool:
    return resume_graph_pipeline(run_id)
