"""Graph telemetry and status routes."""
from fastapi import APIRouter, BackgroundTasks, HTTPException
from ...core.state import state
from ...core.config import settings

router = APIRouter()

@router.get("/api/graph/status")
def get_graph_status():
    """Get the current telemetry and checkpoint status of the LangGraph orchestrator."""
    run_id = state.graph_run_id or ""
    current_node = "idle"
    retries = {}
    is_paused_hitl = (state.pipeline_status == "waiting_spec_approval")
    
    # 1. Check if any node is currently executing in memory
    for node, status in state.graph_node_status.items():
        if status == "executing":
            current_node = node
            break
            
    # 2. Check checkpointer for next node / retries if langgraph is available
    from ...pipeline.graph_orchestrator import LANGGRAPH_AVAILABLE
    if LANGGRAPH_AVAILABLE and run_id:
        try:
            from ...pipeline.graph_orchestrator import _run_with_saver
            config = {"configurable": {"thread_id": run_id}}
            def _get_status(app):
                state_info = app.get_state(config)
                nonlocal current_node, retries
                if state_info and state_info.values:
                    retries = state_info.values.get("retries", {})
                    if current_node == "idle" and state_info.next:
                        current_node = state_info.next[0]
            _run_with_saver(_get_status)
        except Exception:
            pass

    return {
        "run_id": run_id,
        "current_node": current_node,
        "node_status": state.graph_node_status,
        "retries": retries,
        "last_error": state.graph_last_error,
        "is_paused_hitl": is_paused_hitl
    }


@router.post("/api/graph/hitl/approve")
def approve_hitl(background_tasks: BackgroundTasks):
    """Resume the graph after Human-in-the-Loop approval of destructive action."""
    from ...pipeline.graph_orchestrator import resume_graph_pipeline, is_graph_mode_available
    if not is_graph_mode_available() or not state.graph_run_id:
        raise HTTPException(status_code=400, detail="No hay ejecución de grafo activa.")
    state.launcher_logs.append("✅ [HITL] Acción aprobada por usuario. Reanudando...")
    background_tasks.add_task(resume_graph_pipeline, state.graph_run_id)
    return {"success": True, "message": "Grafo reanudado tras HITL."}

