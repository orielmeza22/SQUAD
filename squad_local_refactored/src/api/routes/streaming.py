"""Streaming endpoints (Server-Sent Events).

Migrated 1:1 from the legacy monolith ``api_stream_logs``.
"""

import json
import asyncio

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from ...core.state import state

router = APIRouter()


@router.get("/api/stream-logs")
async def api_stream_logs():
    """SSE stream emitting ``pipeline_logs``, ``launcher_logs`` and ``file_change`` events."""
    async def log_generator():
        last_pipeline_len = 0
        last_pipeline_last_element = None
        last_launcher_len = 0
        last_launcher_last_element = None

        # Initial sends
        p_data = json.dumps({
            "logs": state.logs,
            "is_running": state.is_running,
            "pipeline_status": state.pipeline_status
        })
        yield f"event: pipeline_logs\ndata: {p_data}\n\n"

        is_active = state.active_process and state.active_process.poll() is None
        l_data = json.dumps({
            "logs": state.launcher_logs,
            "is_active": is_active,
            "active_port": getattr(state, "active_port", 5000),
            "active_diagnostic": state.active_diagnostic
        })
        yield f"event: launcher_logs\ndata: {l_data}\n\n"

        last_pipeline_len = len(state.logs)
        last_pipeline_last_element = state.logs[-1] if state.logs else None
        last_launcher_len = len(state.launcher_logs)
        last_launcher_last_element = state.launcher_logs[-1] if state.launcher_logs else None
        last_graph_node_status = None
        last_graph_last_error = None
        last_graph_status = state.pipeline_status
        last_graph_retries = {}

        # Initial graph status send
        initial_graph_status = getattr(state, "graph_node_status", {})
        init_run_id = getattr(state, "graph_run_id", None)
        init_retries = {}
        from ...pipeline.graph_orchestrator import LANGGRAPH_AVAILABLE
        if LANGGRAPH_AVAILABLE and init_run_id:
            try:
                from ...pipeline.graph_orchestrator import _run_with_saver
                config = {"configurable": {"thread_id": init_run_id}}
                def _get_init_status(app):
                    nonlocal init_retries
                    state_info = app.get_state(config)
                    if state_info and state_info.values:
                        init_retries = state_info.values.get("retries", {})
                _run_with_saver(_get_init_status)
            except Exception:
                pass

        g_init = json.dumps({
            "run_id": init_run_id,
            "current_node": "idle",
            "node_status": initial_graph_status,
            "retries": init_retries,
            "last_error": getattr(state, "graph_last_error", None),
            "is_paused_hitl": state.pipeline_status == "waiting_hitl_approval",
            "pipeline_status": state.pipeline_status,
        })
        yield f"event: graph_status\ndata: {g_init}\n\n"
        last_graph_retries = dict(init_retries)

        try:
            while True:
                pipeline_changed = (len(state.logs) != last_pipeline_len) or (
                    len(state.logs) > 0 and state.logs[-1] != last_pipeline_last_element
                )
                is_active = state.active_process and state.active_process.poll() is None
                launcher_changed = (len(state.launcher_logs) != last_launcher_len) or (
                    len(state.launcher_logs) > 0 and state.launcher_logs[-1] != last_launcher_last_element
                )

                if pipeline_changed:
                    p_data = json.dumps({
                        "logs": state.logs,
                        "is_running": state.is_running,
                        "pipeline_status": state.pipeline_status
                    })
                    yield f"event: pipeline_logs\ndata: {p_data}\n\n"
                    last_pipeline_len = len(state.logs)
                    last_pipeline_last_element = state.logs[-1] if state.logs else None

                if launcher_changed:
                    l_data = json.dumps({
                        "logs": state.launcher_logs,
                        "is_active": is_active,
                        "active_port": getattr(state, "active_port", 5000),
                        "active_diagnostic": state.active_diagnostic
                    })
                    yield f"event: launcher_logs\ndata: {l_data}\n\n"
                    last_launcher_len = len(state.launcher_logs)
                    last_launcher_last_element = state.launcher_logs[-1] if state.launcher_logs else None

                # Graph status events (LangGraph telemetry)
                graph_node_status = getattr(state, "graph_node_status", {})
                graph_last_error = getattr(state, "graph_last_error", None)
                run_id = getattr(state, "graph_run_id", None)
                retries = {}
                from ...pipeline.graph_orchestrator import LANGGRAPH_AVAILABLE
                if LANGGRAPH_AVAILABLE and run_id:
                    try:
                        from ...pipeline.graph_orchestrator import _run_with_saver
                        config = {"configurable": {"thread_id": run_id}}
                        def _get_status(app):
                            nonlocal retries
                            state_info = app.get_state(config)
                            if state_info and state_info.values:
                                retries = state_info.values.get("retries", {})
                        _run_with_saver(_get_status)
                    except Exception:
                        pass

                graph_status_changed = (
                    graph_node_status != last_graph_node_status
                    or graph_last_error != last_graph_last_error
                    or state.pipeline_status != last_graph_status
                    or retries != last_graph_retries
                )
                if graph_status_changed:
                    current_node = "idle"
                    for node, status in graph_node_status.items():
                        if status == "executing":
                            current_node = node
                            break
                    g_data = json.dumps({
                        "run_id": run_id,
                        "current_node": current_node,
                        "node_status": graph_node_status,
                        "retries": retries,
                        "last_error": graph_last_error,
                        "is_paused_hitl": state.pipeline_status == "waiting_hitl_approval",
                        "pipeline_status": state.pipeline_status,
                    })
                    yield f"event: graph_status\ndata: {g_data}\n\n"
                    last_graph_node_status = dict(graph_node_status)
                    last_graph_last_error = graph_last_error
                    last_graph_status = state.pipeline_status
                    last_graph_retries = dict(retries)

                if hasattr(state, "file_changes") and state.file_changes:
                    changes = list(state.file_changes)
                    state.file_changes.clear()
                    yield f"event: file_change\ndata: {json.dumps({'files': changes})}\n\n"

                yield ": keep-alive\n\n"
                await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            print("📡 [SSE] Conexión de logs SSE cerrada por el cliente.")

    return StreamingResponse(log_generator(), media_type="text/event-stream")
