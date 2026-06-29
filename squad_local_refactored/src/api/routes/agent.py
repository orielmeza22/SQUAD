"""Agent orchestration endpoints."""

from fastapi import APIRouter, Body, HTTPException, BackgroundTasks

from ...core.state import state
from ...tools.sys_tools import SysTools
from ...llm.provider import AIProvider
from ...pipeline.graph_orchestrator import (
    run_graph_pipeline,
    resume_after_spec_approval,
    is_graph_mode_available,
)

router = APIRouter()


@router.post("/api/run-agent")
def api_run_agent(background_tasks: BackgroundTasks, data: dict = Body(default={})):
    """Run the multi-agent pipeline Phase 1 (SPEC design) in background."""
    model = data.get('model', 'gemini-2.5-flash')
    goal = data.get('goal', '')

    if not is_graph_mode_available():
        raise HTTPException(status_code=500, detail="LangGraph no está disponible. Verifica la instalación.")

    background_tasks.add_task(run_graph_pipeline, goal, model)
    return "OK"


@router.post("/api/spec/adjust")
def api_spec_adjust(data: dict = Body(default={})):
    """Adjust the generated SPEC.md file with user feedback."""
    feedback = data.get("feedback", "")
    model = data.get("model", "gemini-2.5-flash")
    if not feedback:
        raise HTTPException(status_code=400, detail="Falta el feedback")
    try:
        spec_content = SysTools.read("SPEC.md") or ""
        adjust_prompt = f"""Eres el Agente Arquitecto Senior de SQUAD. El usuario solicita ajustar el plano/especificación técnica actual (SPEC.md) con el siguiente feedback:
'{feedback}'

A continuación se muestra la especificación actual SPEC.md:
---
{spec_content}
---

Reescribe y actualiza la especificación técnica aplicando el feedback del usuario de forma coherente. Retorna la nueva versión completa en Markdown. No escribas introducciones ni explicaciones."""
        new_spec = AIProvider().generate(model=model, prompt=adjust_prompt)
        SysTools.write("SPEC.md", new_spec)
        SysTools.write("ARCHITECTURE.md", new_spec)
        state.launcher_logs.append("🧠 [AGENTE ARQUITECTO]: Especificación SPEC.md actualizada con feedback del usuario.")
        return {"success": True, "spec": new_spec}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/spec/approve")
def api_spec_approve(background_tasks: BackgroundTasks):
    """Approve the SPEC.md and run Phase 2 (code building) in background."""
    if not is_graph_mode_available():
        raise HTTPException(status_code=500, detail="LangGraph no está disponible.")
    if not state.graph_run_id:
        raise HTTPException(status_code=400, detail="No hay ninguna ejecución activa del grafo.")

    background_tasks.add_task(resume_after_spec_approval, state.graph_run_id)
    return {"success": True, "message": "Fase 2 del enjambre (Grafo) iniciada en segundo plano."}


@router.post("/api/agent/spec/approve")
def api_agent_spec_approve(background_tasks: BackgroundTasks):
    """LangGraph SPEC approval endpoint."""
    if not is_graph_mode_available():
        raise HTTPException(status_code=400, detail="LangGraph no está disponible.")
    if not state.graph_run_id:
        raise HTTPException(status_code=400, detail="No hay ninguna ejecución activa del grafo.")

    background_tasks.add_task(resume_after_spec_approval, state.graph_run_id)
    return {"success": True, "message": "Grafo reanudado tras aprobación de especificación."}
