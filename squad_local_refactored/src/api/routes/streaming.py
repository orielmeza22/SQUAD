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

                if hasattr(state, "file_changes") and state.file_changes:
                    changes = list(state.file_changes)
                    state.file_changes.clear()
                    yield f"event: file_change\ndata: {json.dumps({'files': changes})}\n\n"

                yield ": keep-alive\n\n"
                await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            print("📡 [SSE] Conexión de logs SSE cerrada por el cliente.")

    return StreamingResponse(log_generator(), media_type="text/event-stream")
