"""Database Administrator Agent for SQUAD."""

from typing import Dict, Any

from .base import BaseAgent
from .prompts import dba_prompt
from ..tools.sys_tools import SysTools


class DBAAgent(BaseAgent):
    """Agent responsible for database design and management.

    Phase 2 (parallel): generates a portable SQL schema (SQLite/PostgreSQL
    compatible) plus a security report (``SECURITY_REPORT.md``).
    """

    def __init__(self):
        super().__init__(
            name="DBA",
            description="Designs database schemas and manages data operations"
        )

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Design database schema based on requirements.

        Args:
            context: Must contain ``plan``; should contain ``existing_context``.

        Returns:
            Dictionary with ``status``, the raw ``output`` and the list of
            written files.
        """
        plan = context.get("plan", "")
        existing_context = context.get("existing_context", "")
        model = self._resolve_model(context)

        full_prompt = dba_prompt(plan, existing_context)
        output = self.generate(model=model, prompt=full_prompt)

        files: list = []
        if output:
            files = SysTools.extract_and_write_multifile(output)

        return {"status": "success", "output": output, "files": files}
