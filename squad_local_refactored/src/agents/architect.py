"""Architect Agent for SQUAD."""

from typing import Dict, Any

from .base import BaseAgent
from .prompts import architect_prompt
from ..tools.sys_tools import SysTools


class ArchitectAgent(BaseAgent):
    """Agent responsible for system architecture design.

    Phase 1 of the swarm: produces ``SPEC.md`` and ``ARCHITECTURE.md`` from the
    user prompt, web-search context and the host preflight capabilities.
    """

    def __init__(self):
        super().__init__(
            name="Architect",
            description="Designs system architecture and component structure"
        )

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Design system architecture based on requirements.

        Args:
            context: Must contain ``prompt``; should contain ``search_ctx``,
                ``preflight`` and ``existing_context``.

        Returns:
            Dictionary with ``status``, ``plan`` (the generated SPEC) and the
            list of written files.
        """
        prompt = context.get("prompt", "")
        search_ctx = context.get("search_ctx", "")
        preflight = context.get("preflight", {})
        existing_context = context.get("existing_context", "")
        model = self._resolve_model(context)

        full_prompt = architect_prompt(prompt, search_ctx, preflight, existing_context)
        plan = self.generate(model=model, prompt=full_prompt)

        written = []
        try:
            SysTools.write("SPEC.md", plan)
            SysTools.write("ARCHITECTURE.md", plan)
            written = ["SPEC.md", "ARCHITECTURE.md"]
        except Exception:
            pass

        return {"status": "success", "plan": plan, "files": written}
