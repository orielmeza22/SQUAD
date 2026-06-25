"""Backend Agent for SQUAD."""

from typing import Dict, Any

from .base import BaseAgent
from .prompts import backend_prompt
from ..tools.sys_tools import SysTools


class BackendAgent(BaseAgent):
    """Agent responsible for backend code generation.

    Phase 2: generates business logic / APIs / ``main_output.{py,js}`` with
    portable-DB and dynamic-PORT rules.
    """

    def __init__(self):
        super().__init__(
            name="Backend",
            description="Generates backend API and business logic code"
        )

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate backend code based on the plan.

        Args:
            context: Must contain ``plan``; should contain ``existing_context``.

        Returns:
            Dictionary with ``status``, the raw ``output`` and the list of
            written files.
        """
        plan = context.get("plan", "")
        existing_context = context.get("existing_context", "")
        model = self._resolve_model(context)

        full_prompt = backend_prompt(plan, existing_context)
        output = self.generate(model=model, prompt=full_prompt)

        files: list = []
        if output:
            files = SysTools.extract_and_write_multifile(output)

        return {"status": "success", "output": output, "files": files}
