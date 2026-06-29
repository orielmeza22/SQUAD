"""Pipeline modules for SQUAD.

- :mod:`graph_orchestrator` — LangGraph multi-agent swarm (Phase 1 SPEC + Phase 2 build).
- :mod:`self_heal` — autonomous linter and runtime watchdog.
- :mod:`launcher` — app launch sequence and listening-port enumeration.
- :mod:`installer` — winget-based tool auto-installation.
"""

from . import self_heal
from . import launcher
from . import installer

__all__ = ["self_heal", "launcher", "installer"]
