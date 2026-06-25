"""Agent modules for SQUAD."""

from .base import BaseAgent
from .architect import ArchitectAgent
from .dba import DBAAgent
from .backend import BackendAgent
from .frontend import FrontendAgent
from .qa import QAAgent
from .devops import DevOpsAgent
from .prompts import (
    architect_prompt,
    dba_prompt,
    frontend_prompt,
    backend_prompt,
    code_review_prompt,
    fix_prompt,
    ux_audit_prompt,
    qa_devops_prompt,
    linter_prompt,
    style_memory_str,
)

__all__ = [
    "BaseAgent",
    "ArchitectAgent",
    "DBAAgent",
    "BackendAgent",
    "FrontendAgent",
    "QAAgent",
    "DevOpsAgent",
    "architect_prompt",
    "dba_prompt",
    "frontend_prompt",
    "backend_prompt",
    "code_review_prompt",
    "fix_prompt",
    "ux_audit_prompt",
    "qa_devops_prompt",
    "linter_prompt",
    "style_memory_str",
]
