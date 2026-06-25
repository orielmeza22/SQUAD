"""System auto-installer (winget on Windows).

Migrated 1:1 from the legacy monolith ``run_system_installer``.
"""

import sys
import subprocess
from typing import Tuple

from ..core.state import state


def run_system_installer(tool_name: str) -> Tuple[bool, str]:
    """Auto-install a tool via winget (Windows only).

    Args:
        tool_name: One of ``node``, ``git``, ``docker``.

    Returns:
        Tuple of (success, message).
    """
    tool_map = {
        "node": "OpenJS.NodeJS",
        "git": "Git.Git",
        "docker": "Docker.DockerDesktop"
    }

    winget_id = tool_map.get(tool_name.lower())
    if not winget_id:
        return False, f"Herramienta '{tool_name}' no soportada para auto-instalación."

    if sys.platform != 'win32':
        return False, "La auto-instalación por ahora solo está soportada en Windows (vía winget)."

    ps_cmd = f"Start-Process winget -ArgumentList 'install --id {winget_id} -e --accept-source-agreements --accept-package-agreements'"
    cmd = f"powershell -Command \"{ps_cmd}\""

    state.launcher_logs.append(f"[AUTO-INSTALADOR] Lanzando instalador de {tool_name}...")
    state.launcher_logs.append("[AUTO-INSTALADOR] ⚠️ Sigue el progreso en la ventana externa de consola que se abrirá en tu pantalla.")

    try:
        subprocess.run(cmd, shell=True, check=True)
        state.launcher_logs.append(f"[AUTO-INSTALADOR] ✅ Ventana de instalación de {tool_name} abierta correctamente.")
        state.launcher_logs.append("[AUTO-INSTALADOR] Presiona 'REFRESCAR' en el panel de Pre-flight una vez que finalice la instalación en la ventana externa.")
        return True, f"Lanzado instalador de {tool_name}."
    except Exception as e:
        state.launcher_logs.append(f"[AUTO-INSTALADOR] ❌ Falló al lanzar el instalador: {e}")
        return False, str(e)
