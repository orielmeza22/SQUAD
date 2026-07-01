"""Base agent class for SQUAD."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from ..core.state import state
from ..llm.provider import AIProvider


class BaseAgent(ABC):
    """Abstract base class for all SQUAD agents.

    Subclasses implement :meth:`execute`, which receives a ``context`` dict
    (containing the user prompt, plan, model, etc.) and returns a result dict.
    Agents generate text via the shared :class:`AIProvider` and persist files
    through :class:`SysTools`.
    """

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    def _resolve_model(self, context: Dict[str, Any]) -> str:
        """Pick the target model for this run (context override → global state)."""
        return context.get("target_model") or context.get("model") or getattr(state, "active_model", "gemini-2.5-flash")

    def generate(self, model: str, prompt: str, is_json: bool = False) -> str:
        """Generate text via the unified AI provider."""
        return AIProvider().generate(model=model, prompt=prompt, is_json=is_json, agent_name=self.name)

    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent's task.

        Args:
            context: Dictionary containing task context and parameters
                (e.g. ``prompt``, ``plan``, ``model``, ``target_model``,
                ``search_ctx``, ``existing_context``).

        Returns:
            Dictionary containing execution results.
        """
        raise NotImplementedError

    def validate_input(self, context: Dict[str, Any]) -> bool:
        """Validate input context before execution."""
        return True

    def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        return {"name": self.name, "description": self.description, "status": "ready"}
