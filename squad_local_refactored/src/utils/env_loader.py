"""Environment loader (.env / .env.local into os.environ).

Migrated 1:1 from the legacy monolith ``load_env``.
"""

import os
from typing import List


def _candidate_env_paths() -> List[str]:
    """Return the ordered list of directories to search for ``.env`` files."""
    backend_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    workspace = os.path.join(backend_root, "SQUAD_WORKSPACE")
    return [
        os.path.dirname(backend_root),  # repo root
        backend_root,                    # squad_local_refactored/
        workspace,                       # SQUAD_WORKSPACE/
    ]


def load_env() -> None:
    """Load ``.env`` / ``.env.local`` from candidate directories into ``os.environ``."""
    for path in _candidate_env_paths():
        for fn in [".env", ".env.local"]:
            p = os.path.join(path, fn)
            if os.path.exists(p):
                print(f"📡 [ENV] Cargando variables desde: {p}")
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith("#") and "=" in line:
                                k, v = line.split("=", 1)
                                os.environ[k.strip()] = v.strip().strip('"\'')
                except Exception as e:
                    print(f"Error cargando variables desde {p}: {e}")


# Load on import, mirroring the legacy behavior.
load_env()
