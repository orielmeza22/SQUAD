"""Frontend Agent for SQUAD."""

from typing import Dict, Any

from .base import BaseAgent
from .prompts import frontend_prompt
from ..tools.sys_tools import SysTools


class FrontendAgent(BaseAgent):
    """Agent responsible for frontend/UI generation.

    Phase 2 (parallel): generates ``index.html``, ``styles.css`` and ``app.js``
    following strict HTML5 + relative-path + CDN rules.
    """

    def __init__(self):
        super().__init__(
            name="Frontend",
            description="Generates frontend UI components and styles"
        )

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate frontend UI based on the plan.

        Args:
            context: Must contain ``plan``; should contain ``existing_context``
                and ``style_mem_str``.

        Returns:
            Dictionary with ``status``, the raw ``output`` and the list of
            written files.
        """
        plan = context.get("plan", "")
        existing_context = context.get("existing_context", "")
        style_mem_str = context.get("style_mem_str", "")
        model = self._resolve_model(context)

        full_prompt = frontend_prompt(plan, existing_context, style_mem_str, stack=context.get("stack", "FASTAPI_HTMX"))
        output = self.generate(model=model, prompt=full_prompt)

        files: list = []
        if output:
            files = SysTools.extract_and_write_multifile(output)

        return {"status": "success", "output": output, "files": files}
