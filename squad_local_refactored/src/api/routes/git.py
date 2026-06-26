"""Git endpoints.

Migrated 1:1 from the legacy monolith: ``api_get_git_file_history``,
``api_get_git_history``, ``api_github_publish``, ``api_revert``,
``api_git_checkout``, ``api_git_restore_head``, ``api_get_commits``.
"""

import subprocess

from fastapi import APIRouter, Body, Query, HTTPException

from ...core.state import state
from ...tools.sys_tools import SysTools
from ...tools.github import github_publish

router = APIRouter()


@router.get("/api/git/file-history")
def api_get_git_file_history(file: str = Query(...)):
    """Return the content of a file at HEAD."""
    try:
        res = subprocess.run(
            ["git", "show", f"HEAD:{file}"],
            cwd=SysTools.WORKSPACE, capture_output=True, text=True, shell=True
        )
        content = res.stdout if res.returncode == 0 else ""
        return {"success": True, "content": content}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/api/git/history")
def api_get_git_history():
    """Return the last 20 commits (hash/message/time)."""
    try:
        res = subprocess.run(
            ["git", "log", "--pretty=format:%h|%s|%ar", "-n", "20"],
            cwd=SysTools.WORKSPACE, capture_output=True, text=True, shell=True
        )
        commits = []
        if res.returncode == 0 and res.stdout.strip():
            for line in res.stdout.strip().split("\n"):
                if "|" in line:
                    parts = line.split("|", 2)
                    commits.append({"hash": parts[0], "message": parts[1], "time": parts[2]})
        return {"success": True, "commits": commits}
    except Exception as e:
        return {"success": False, "error": str(e), "commits": []}


@router.post("/api/git/github-publish")
def api_github_publish(data: dict = Body(default={})):
    """Create a GitHub repo from the workspace and push it."""
    token = data.get('token', '')
    repo_name = data.get('repo_name', '')
    private = data.get('private', False)
    ok, msg = github_publish(token, repo_name, private)
    return {"success": ok, "message": msg}


@router.post("/api/git/revert")
def api_revert(data: dict = Body(default={})):
    """Hard-reset the workspace to a given commit."""
    commit_hash = data.get('hash', '')
    if not commit_hash:
        raise HTTPException(status_code=400, detail="Falta el hash del commit")
    with SysTools.git_lock:
        try:
            res = subprocess.run(
                ["git", "reset", "--hard", commit_hash],
                cwd=SysTools.WORKSPACE, capture_output=True, text=True, shell=True
            )
            if res.returncode == 0:
                return {"success": True, "message": f"Workspace revertido al commit {commit_hash}"}
            else:
                return {"success": False, "message": res.stderr}
        except Exception as e:
            return {"success": False, "message": str(e)}


@router.post("/api/git/checkout")
def api_git_checkout(data: dict = Body(default={})):
    """Checkout a commit in preview mode (detached HEAD)."""
    commit_hash = data.get('hash', '')
    if not commit_hash:
        raise HTTPException(status_code=400, detail="Falta el hash del commit")
    with SysTools.git_lock:
        try:
            res = subprocess.run(
                ["git", "checkout", "-f", commit_hash],
                cwd=SysTools.WORKSPACE, capture_output=True, text=True, shell=True
            )
            if res.returncode == 0:
                state.file_changes.append("*")
                state.launcher_logs.append(f"⏱️ [TIMETRAVEL]: Workspace cambiado al snapshot del commit {commit_hash} (Modo Vista Previa).")
                return {"success": True, "message": f"Workspace en modo vista previa del commit {commit_hash}"}
            else:
                return {"success": False, "message": res.stderr}
        except Exception as e:
            return {"success": False, "message": str(e)}


@router.post("/api/git/restore-head")
def api_git_restore_head():
    """Restore the workspace to the main/master branch HEAD."""
    with SysTools.git_lock:
        try:
            res = subprocess.run(
                ["git", "checkout", "-f", "main"],
                cwd=SysTools.WORKSPACE, capture_output=True, text=True, shell=True
            )
            if res.returncode != 0:
                # Try master if main doesn't exist
                res = subprocess.run(
                    ["git", "checkout", "-f", "master"],
                    cwd=SysTools.WORKSPACE, capture_output=True, text=True, shell=True
                )
            if res.returncode == 0:
                state.file_changes.append("*")
                state.launcher_logs.append("⏱️ [TIMETRAVEL]: Regresaste al estado actual de la rama principal (HEAD).")
                return {"success": True, "message": "Volviste al estado actual (HEAD)."}
            else:
                return {"success": False, "message": res.stderr}
        except Exception as e:
            return {"success": False, "message": str(e)}


@router.get("/api/git/commits")
def api_get_commits():
    """Return the last 30 commits (oneline)."""
    try:
        res = subprocess.run(
            ["git", "log", "--oneline", "-n", "30"],
            cwd=SysTools.WORKSPACE, capture_output=True, text=True, shell=True
        )
        commits = []
        if res.returncode == 0:
            for line in res.stdout.splitlines():
                if line.strip():
                    parts = line.strip().split(" ", 1)
                    commit_hash = parts[0]
                    msg = parts[1] if len(parts) > 1 else ""
                    commits.append({"hash": commit_hash, "message": msg})
        return {"success": True, "commits": commits}
    except Exception as e:
        return {"success": False, "error": str(e)}
