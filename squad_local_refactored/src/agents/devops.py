"""DevOps Agent for SQUAD."""

from typing import Dict, Any

from .base import BaseAgent
from ..tools.sys_tools import SysTools


class DevOpsAgent(BaseAgent):
    """Agent responsible for deployment, infrastructure and shadow Git.

    Phase 2 (final step): commits the workspace snapshot via the shadow Git
    built into :class:`SysTools`.
    """

    def __init__(self):
        super().__init__(
            name="DevOps",
            description="Manages deployment, containers, and infrastructure"
        )

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create a shadow Git commit for the generated workspace.

        Args:
            context: May contain ``commit_message`` (defaults to the
                standard auto-commit message).

        Returns:
            Dictionary with ``status`` and Git commit result.
        """
        msg = context.get("commit_message", "Auto-commit: Workspace AI V7 Multi-Agent")
        ok, git_msg = SysTools.git_init_and_commit(msg)
        return {"status": "success" if ok else "error", "git_result": git_msg}
