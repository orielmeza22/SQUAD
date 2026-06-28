"""Global state management for the SQUAD application."""

import threading
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field


@dataclass
class PipelineState:
    """Global state for tracking pipeline execution, logs, and diagnostics."""
    
    # Pipeline status
    logs: List[str] = field(default_factory=list)
    is_running: bool = False
    pipeline_status: str = "idle"  # idle | running | waiting_spec_approval | waiting_hitl_approval
    pending_pipeline_data: Dict[str, Any] = field(default_factory=dict)
    
    # Diagnostics
    active_diagnostic: Optional[Dict[str, str]] = None  # {error, file, line, suggestion}
    linter_retries: int = 0
    
    # Design identity (can be overridden from settings)
    design_identity: Dict[str, str] = field(default_factory=lambda: {
        "colors": "Dark elegant (slate, emerald accents)",
        "fonts": "Inter, System Font",
        "style": "Modern Minimalist",
        "preset": "default"
    })
    
    # Smart routing flag
    smart_routing: bool = False
    
    # Launcher state
    active_port: int = 5000
    default_port: int = 5000
    file_changes: List[str] = field(default_factory=list)
    launcher_logs: List[str] = field(default_factory=list)
    active_process: Optional[Any] = None  # subprocess.Popen
    
    # LLM state
    active_model: str = "gemini-2.5-flash"
    temperature: float = 0.3
    system_prompt: str = "Eres el Orquestador V5. Responde siempre en JSON."
    context_window: int = 16384
    
    # Token and cost tracking
    token_in: int = 0
    token_out: int = 0
    cost_usd: float = 0.0
    cache_hits: int = 0
    
    # Feature flags
    enable_rag: bool = True
    interception_enabled: bool = True
    
    # Pending writes (for critical file interception)
    pending_writes: Dict[str, str] = field(default_factory=dict)
    
    # Chat history
    chat_history: List[Dict[str, str]] = field(default_factory=list)
    
    # LangGraph state
    graph_run_id: Optional[str] = None        # ID del run actual para reanudar
    graph_node_status: Dict[str, str] = field(default_factory=dict)  # {agent_name: "thinking"|"executing"|"error"|"done"|"paused_hitl"}
    graph_last_error: Optional[str] = None    # último error reportado por QA/reviewer

    def set_node_status(self, node: str, status: str) -> None:
        self.graph_node_status[node] = status
        self.log(f"[{node}] → {status}")
    
    def log(self, message: str) -> None:
        """Add a message to the logs and print it."""
        try:
            print(message)
        except Exception:
            try:
                # Safe print fallback using ascii/replace
                print(message.encode('ascii', errors='replace').decode('ascii'))
            except Exception:
                pass
        self.logs.append(message)

    
    def update_last_log(self, message: str) -> None:
        """Update the last log entry with a new message."""
        if self.logs:
            self.logs[-1] = message
        else:
            self.logs.append(message)
    
    def clear_logs(self) -> None:
        """Clear all logs."""
        self.logs.clear()
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status as a dictionary."""
        return {
            "is_running": self.is_running,
            "pipeline_status": self.pipeline_status,
            "active_model": self.active_model,
            "active_port": self.active_port,
            "token_in": self.token_in,
            "token_out": self.token_out,
            "cost_usd": self.cost_usd,
            "cache_hits": self.cache_hits,
            "linter_retries": self.linter_retries,
        }


# Global state instance (thread-safe access via module-level lock if needed)
state = PipelineState()

# Thread lock for state modifications (optional, for complex concurrent scenarios)
state_lock = threading.Lock()
