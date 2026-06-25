"""Base agent class for SQUAD."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseAgent(ABC):
    """Abstract base class for all SQUAD agents."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent's task.
        
        Args:
            context: Dictionary containing task context and parameters
            
        Returns:
            Dictionary containing execution results
        """
        pass
    
    def validate_input(self, context: Dict[str, Any]) -> bool:
        """Validate input context before execution.
        
        Args:
            context: Dictionary containing task context and parameters
            
        Returns:
            True if valid, False otherwise
        """
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status.
        
        Returns:
            Dictionary with agent status information
        """
        return {
            "name": self.name,
            "description": self.description,
            "status": "ready"
        }
