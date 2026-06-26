"""LLM endpoints: telemetry, vault, providers, ollama pull, prompt optimize, chat.

Migrated 1:1 from the legacy monolith.
"""

import os
import json
import subprocess
import threading

from fastapi import APIRouter, Body, HTTPException

from ...core.state import state
from ...llm.provider import AIProvider
from ...llm.ollama import OllamaProvider
from ...llm.gemini import GeminiProvider
from ...llm.openai import OpenAIProvider
from ...llm.openrouter import OpenRouterProvider
from ...tools.cache import OptTools
from ...tools.sys_tools import SysTools

router = APIRouter()

# Vault file lives alongside the backend package (mirrors legacy BASE_DIR).
_VAULT_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "prompts_vault.json"
)


@router.get("/api/llm/telemetry")
def api_get_llm_telemetry():
    """Return token usage, cost and cache hits."""
    return {
        "token_in": state.token_in,
        "token_out": state.token_out,
        "cost_usd": getattr(state, "cost_usd", 0.0),
        "cache_hits": getattr(state, "cache_hits", 0)
    }


def _read_vault() -> list:
    if os.path.exists(_VAULT_FILE):
        try:
            with open(_VAULT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def _write_vault(prompts: list) -> None:
    with open(_VAULT_FILE, "w", encoding="utf-8") as f:
        json.dump(prompts, f, ensure_ascii=False, indent=2)


@router.get("/api/llm/vault")
def api_get_vault_prompts():
    """Return saved prompts from the vault."""
    try:
        return {"success": True, "prompts": _read_vault()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/llm/vault")
def api_save_prompt(data: dict = Body(default={})):
    """Append a prompt to the vault."""
    try:
        prompt_to_save = data.get("prompt", "")
        prompts = _read_vault()
        if prompt_to_save and prompt_to_save not in prompts:
            prompts.append(prompt_to_save)
            _write_vault(prompts)
        return {"success": True, "prompts": prompts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/llm/vault/delete")
def api_delete_prompt(data: dict = Body(default={})):
    """Remove a prompt from the vault."""
    try:
        prompt_to_delete = data.get("prompt", "")
        prompts = _read_vault()
        if prompt_to_delete in prompts:
            prompts.remove(prompt_to_delete)
            _write_vault(prompts)
        return {"success": True, "prompts": prompts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/llm/providers")
def api_get_providers():
    """Return availability + model lists for each LLM provider."""
    ollama = OllamaProvider()
    ollama_online = ollama.is_available()
    ollama_models = ollama.list_models() if ollama_online else []

    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")

    providers = []
    providers.append({
        "id": "gemini",
        "name": "Google Gemini (Nube)",
        "available": GeminiProvider(gemini_key).is_available(),
        "models": ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash", "gemini-2.0-flash-exp"]
    })
    providers.append({
        "id": "ollama",
        "name": "Ollama Local",
        "available": ollama_online,
        "models": ollama_models
    })
    providers.append({
        "id": "openai",
        "name": "OpenAI (Nube)",
        "available": OpenAIProvider(openai_key).is_available(),
        "models": ["gpt-4o", "gpt-4o-mini", "o1-mini"]
    })
    providers.append({
        "id": "openrouter",
        "name": "OpenRouter (Nube)",
        "available": OpenRouterProvider(openrouter_key).is_available(),
        "models": ["openrouter/google/gemini-2.5-flash:free",
                   "openrouter/meta-llama/llama-3.1-8b-instruct:free",
                   "openrouter/qwen/qwen-2.5-72b-instruct:free"]
    })
    return {"providers": providers}


@router.post("/api/llm/ollama/pull")
def api_ollama_pull(data: dict = Body(default={})):
    """Background-pull an Ollama model."""
    model = data.get("model", "")
    if not model:
        raise HTTPException(status_code=400, detail="Modelo faltante")
    try:
        def pull_worker():
            state.launcher_logs.append(f"[OLLAMA] Iniciando descarga de modelo: {model}...")
            proc = subprocess.Popen(
                f"ollama pull {model}", shell=True,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                encoding='utf-8', errors='replace'
            )
            for line in proc.stdout:
                state.launcher_logs.append(f"[OLLAMA PULL] {line.strip()}")
            proc.wait()
            state.launcher_logs.append(f"[OLLAMA] Descarga terminada con exit code {proc.returncode}")

        threading.Thread(target=pull_worker, daemon=True).start()
        return {"success": True, "message": f"Iniciando descarga de {model} en segundo plano."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/prompt/optimize")
def api_prompt_optimize(data: dict = Body(default={})):
    """Rewrite a user prompt into a structured agent-swarm prompt."""
    prompt = data.get("prompt", "")
    model = data.get("model", "gemini-2.5-flash")
    if not prompt:
        raise HTTPException(status_code=400, detail="Falta el prompt original")
    try:
        opt_sys = """Eres un experto en ingeniería de prompts y arquitecto de software.
Tu tarea es tomar el prompt simple del usuario y optimizarlo, transformándolo en un prompt de enjambre de agentes IA detallado, estructurado y claro en español.
Define:
1. Objetivo general de la aplicación.
2. Vistas y diseño de la UI (Frontend).
3. Base de datos SQLite requerida (tablas, campos clave).
4. Endpoints y APIs clave (Backend).
5. Reglas de negocio y flujos de validación.

Tu respuesta debe ser únicamente el prompt optimizado, listo para ser copiado y enviado directamente. No incluyas intros ni explicaciones adicionales."""
        res = AIProvider().generate(model=model, prompt=f"{opt_sys}\n\nPrompt original del usuario:\n'{prompt}'")
        return {"success": True, "optimized": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/chat")
def api_chat(data: dict = Body(default={})):
    """Chat endpoint supporting general/architect/qa/devops/debate targets."""
    model = data.get('model', 'llama3:latest')
    msg = data.get('message', '')
    target = data.get('target', 'general')

    if msg:
        state.chat_history.append({"role": "user", "content": msg})
        files_ctx_str = OptTools.get_relevant_files_context(msg)

        if target == 'debate':
            try:
                arch_prompt = (f"Eres el Agente Arquitecto de SQUAD. El usuario nos consulta/pide:\n'{msg}'\n\n"
                               f"Los archivos actuales del proyecto son:\n{files_ctx_str}\n\n"
                               f"Propón un diseño arquitectónico o solución conceptual estructurada para abordar esta solicitud.")
                arch_res = AIProvider().generate(model=model, prompt=arch_prompt)

                dev_prompt = (f"Eres el Agente Desarrollador Full-Stack de SQUAD. El Agente Arquitecto propone la siguiente "
                              f"solución para la consulta del usuario:\n{arch_res}\n\nAnaliza la propuesta del Arquitecto, "
                              f"debátela críticamente indicando qué consideraciones de código o dependencias son necesarias, "
                              f"y propón cómo implementarla en el proyecto.")
                dev_res = AIProvider().generate(model=model, prompt=dev_prompt)

                debate_log = (f"💬 [DEBATE DE AGENTES INICIADO]\n\n🧠 [AGENTE ARQUITECTO]:\n{arch_res}\n\n"
                              f"💻 [AGENTE DESARROLLADOR]:\n{dev_res}")
                state.chat_history.append({"role": "assistant", "content": debate_log})
            except Exception as e:
                state.chat_history.append({"role": "assistant", "content": f"Fallo en debate: {e}"})
        else:
            system_ctx = (
                "Eres un agente inteligente dentro del ecosistema SQUAD (Software Quick Autonomous Development).\n"
                "SQUAD es una plataforma para la generación, ejecución y autocuración autónoma de aplicaciones locales en la PC del usuario.\n"
                "Tu objetivo es ayudar al usuario a entender, construir, desplegar o modificar la aplicación en su máquina local.\n"
                "La arquitectura actual de SQUAD consta de:\n"
                "1. Un backend en Python con FastAPI sirviendo como orquestador y sirviendo las APIs en http://localhost:8000.\n"
                "2. Una UI web en React/Vite para el dashboard y la interacción.\n"
                "3. Un Workspace local aislado (SQUAD_WORKSPACE) donde se aloja el código de la app generada por el usuario (Node.js, Express, Python, FastAPI, SQLite, etc.).\n"
                "Cuando el usuario hable del 'sistema' o 'app squad', se refiere a este ecosistema en el que estás ejecutándote actualmente."
            )
            if target == 'architect':
                system_ctx += "\nActúas como el Agente Arquitecto. Concéntrate en la estructura general, patrones de diseño y decisiones arquitectónicas."
            elif target == 'qa':
                system_ctx += "\nActúas como el Agente Senior QA. Concéntrate en diseñar planes de prueba, encontrar casos límite, bugs y escribir tests."
            elif target == 'devops':
                system_ctx += "\nActúas como el Agente DevOps. Concéntrate en configurar Docker, dependencias, scripts de ejecución, CI/CD y automatizaciones."

            system_ctx += f"\n\nLos archivos actuales del proyecto en el workspace son:\n{files_ctx_str}"
            system_ctx += f"\n\n{OptTools.CODE_GUIDELINES}"

            messages = [{"role": "system", "content": system_ctx}] + state.chat_history[:-1] + [{"role": "user", "content": msg}]
            try:
                response_text = AIProvider().generate(model=model, messages=messages)
                modified_files = SysTools.extract_and_write_multifile(response_text)
                if modified_files:
                    SysTools.git_init_and_commit(f"Chat-update: {', '.join(modified_files)}")
                    state.chat_history.append({"role": "system", "content": f"SQUAD: Se actualizaron los archivos: {', '.join(modified_files)} en el workspace."})
                state.chat_history.append({"role": "assistant", "content": response_text})
            except Exception as e:
                state.chat_history.append({"role": "assistant", "content": f"Error: {e}"})
    return {"history": state.chat_history}
