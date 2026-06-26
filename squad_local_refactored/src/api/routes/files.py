"""File management endpoints.

Migrated 1:1 from the legacy monolith: ``api_get_files``, ``api_open_explorer``,
``api_clear_workspace``, ``api_create_file``, ``api_delete_file``, ``api_rename_file``,
``api_save_file``, ``api_format``.
"""

import os
import shutil
import platform
import subprocess

from fastapi import APIRouter, Body, HTTPException

from ...core.state import state
from ...tools.sys_tools import SysTools, sanitize_workspace_path
from ...tools.formatter import format_file
from ...utils.env_loader import load_env

router = APIRouter()


@router.get("/api/files")
def api_get_files():
    """Return all workspace files and their contents (recursive, skips noise dirs)."""
    files_data = {}
    if os.path.exists(SysTools.WORKSPACE):
        for root, _, files in os.walk(SysTools.WORKSPACE):
            if ".git" in root or "node_modules" in root or "__pycache__" in root:
                continue
            for f in files:
                p = os.path.join(root, f)
                rel = os.path.relpath(p, SysTools.WORKSPACE).replace('\\', '/')
                content = SysTools.read(rel)
                if content is not None:
                    files_data[rel] = content
    return {"files": files_data}


@router.post("/api/fs/open-explorer")
async def api_open_explorer():
    """Open the workspace in the OS file explorer."""
    try:
        system = platform.system()
        if system == "Windows":
            subprocess.Popen(["explorer", SysTools.WORKSPACE])
        elif system == "Darwin":
            subprocess.Popen(["open", SysTools.WORKSPACE])
        else:
            subprocess.Popen(["xdg-open", SysTools.WORKSPACE])
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/fs/clear-workspace")
def api_clear_workspace():
    """Wipe the workspace (keep ``.git``) and reset transient state."""
    try:
        if state.active_process and state.active_process.poll() is None:
            try:
                SysTools.kill_process_tree(state.active_process.pid)
            except Exception:
                pass
            state.active_process = None

        SysTools.cleanup_workspace_processes()

        state.pending_writes = {}
        state.chat_history = []
        state.logs = []
        state.launcher_logs = []
        state.active_diagnostic = None

        if os.path.exists(SysTools.WORKSPACE):
            for item in os.listdir(SysTools.WORKSPACE):
                if item == ".git":
                    continue
                path = os.path.join(SysTools.WORKSPACE, item)
                try:
                    if os.path.isdir(path):
                        shutil.rmtree(path, ignore_errors=True)
                    else:
                        os.remove(path)
                except Exception as ex:
                    print(f"Error removing {path}: {ex}")

        SysTools.git_init_and_commit("Clean workspace snapshot")
        return {"success": True, "message": "Workspace limpiado completamente."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/fs/create")
def api_create_file(data: dict = Body(default={})):
    """Create a file or directory inside the workspace."""
    path_param = data.get('path', '')
    is_dir = data.get('is_dir', False)
    if not path_param:
        raise HTTPException(status_code=400, detail="Ruta vacía")
    try:
        full_path = sanitize_workspace_path(path_param)
        if is_dir:
            os.makedirs(full_path, exist_ok=True)
        else:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            if not os.path.exists(full_path):
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write('')
        SysTools.git_init_and_commit(f"Created {'directory' if is_dir else 'file'}: {path_param}")
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/fs/delete")
def api_delete_file(data: dict = Body(default={})):
    """Delete a file or directory inside the workspace."""
    path_param = data.get('path', '')
    if not path_param:
        raise HTTPException(status_code=400, detail="Ruta vacía")
    try:
        full_path = sanitize_workspace_path(path_param)
        if os.path.exists(full_path):
            if os.path.isdir(full_path):
                shutil.rmtree(full_path, ignore_errors=True)
            else:
                os.remove(full_path)
        SysTools.git_init_and_commit(f"Deleted: {path_param}")
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/fs/rename")
def api_rename_file(data: dict = Body(default={})):
    """Rename/move a file or directory inside the workspace."""
    old_param = data.get('old_path', '')
    new_param = data.get('new_path', '')
    if not old_param or not new_param:
        raise HTTPException(status_code=400, detail="Rutas inválidas")
    try:
        old_full = sanitize_workspace_path(old_param)
        new_full = sanitize_workspace_path(new_param)
        os.makedirs(os.path.dirname(new_full), exist_ok=True)
        os.rename(old_full, new_full)
        SysTools.git_init_and_commit(f"Renamed {old_param} to {new_param}")
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/save_file")
def api_save_file(data: dict = Body(default={})):
    """Force-write a file (bypassing critical-file interception)."""
    name = data.get('name', '')
    content = data.get('content', '')
    if not name:
        raise HTTPException(status_code=400, detail="Nombre de archivo vacío")
    try:
        SysTools.write(name, content, force=True)
        if name == ".env" or name.endswith(".env"):
            load_env()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/format")
def api_format(data: dict = Body(default={})):
    """Write + format a file, returning the formatted content."""
    name = data.get('name', '')
    content = data.get('content', '')
    if not name:
        raise HTTPException(status_code=400, detail="Nombre de archivo vacío")
    try:
        full_path = sanitize_workspace_path(name)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        ok, msg = format_file(full_path)
        with open(full_path, 'r', encoding='utf-8') as f:
            formatted_content = f.read()
        SysTools.git_init_and_commit(f"Formatted and saved file: {name}")
        return {"success": True, "message": msg, "content": formatted_content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
