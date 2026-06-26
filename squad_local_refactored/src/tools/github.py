"""GitHub publishing helper (create repo + push).

Migrated 1:1 from the legacy monolith ``github_publish``.
"""

import os
import json
import subprocess
import urllib.request
import urllib.error
from typing import Tuple

from ..tools.sys_tools import SysTools


def github_publish(token: str, repo_name: str, private: bool = False) -> Tuple[bool, str]:
    """Create a GitHub repo from the workspace and push it.

    Args:
        token: GitHub personal access token.
        repo_name: Name of the repository to create.
        private: Whether the repo should be private.

    Returns:
        Tuple of (success, message).
    """
    try:
        req = urllib.request.Request(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "SQUAD-App-Builder"
            }
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            user_data = json.loads(r.read().decode('utf-8'))
            username = user_data.get('login')
    except Exception as e:
        return False, f"Error obteniendo usuario de GitHub (Verifica tu Token): {e}"

    if not username:
        return False, "No se pudo determinar el nombre de usuario de GitHub."

    html_url = None
    try:
        payload = {"name": repo_name, "private": private}
        req = urllib.request.Request(
            "https://api.github.com/user/repos",
            data=json.dumps(payload).encode('utf-8'),
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json",
                "User-Agent": "SQUAD-App-Builder"
            }
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            res_data = json.loads(r.read().decode('utf-8'))
            html_url = res_data.get('html_url')
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8')
        try:
            err_json = json.loads(err_body)
            msg = err_json.get('message', '')
        except Exception:
            msg = err_body
        if e.code == 422 and "already exists" in msg:
            html_url = f"https://github.com/{username}/{repo_name}"
        else:
            return False, f"Error de GitHub API ({e.code}): {msg}"
    except Exception as e:
        return False, f"Error creando el repositorio: {e}"

    try:
        if not os.path.exists(os.path.join(SysTools.WORKSPACE, ".git")):
            subprocess.run(["git", "init"], cwd=SysTools.WORKSPACE, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Squad AI"], cwd=SysTools.WORKSPACE, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "squad@ai.local"], cwd=SysTools.WORKSPACE, check=True, capture_output=True)

        subprocess.run(["git", "add", "."], cwd=SysTools.WORKSPACE, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Graduation to GitHub from SQUAD"], cwd=SysTools.WORKSPACE, capture_output=True)

        remote_url = f"https://{username}:{token}@github.com/{username}/{repo_name}.git"
        subprocess.run(["git", "remote", "remove", "origin"], cwd=SysTools.WORKSPACE, capture_output=True)
        subprocess.run(["git", "remote", "add", "origin", remote_url], cwd=SysTools.WORKSPACE, check=True, capture_output=True)

        subprocess.run(["git", "branch", "-M", "main"], cwd=SysTools.WORKSPACE, check=True, capture_output=True)
        res = subprocess.run(["git", "push", "-u", "origin", "main"], cwd=SysTools.WORKSPACE, check=True, capture_output=True, text=True, shell=True)
        if res.returncode == 0:
            return True, f"Proyecto graduado exitosamente a GitHub: {html_url}"
        else:
            return False, f"Git push falló: {res.stderr}"
    except subprocess.CalledProcessError as e:
        return False, f"Git push falló: {e.stderr}"
    except Exception as e:
        return False, f"Error al empujar cambios: {str(e)}"
