"""Enrich agent context with RAG-relevant code fragments."""
from typing import List, Dict, Optional
from ..core.config import settings
from ..tools.rag_indexer import RAGIndexer
from ..tools.sys_tools import SysTools


def enrich_context(agent_name: str, task: str) -> str:
    """Query RAG for relevant fragments and format as context string.

    Returns empty string if RAG is disabled or unavailable.
    """
    if not getattr(settings, "rag_enabled", False):
        return ""

    indexer = RAGIndexer(SysTools.WORKSPACE, getattr(settings, "rag_collection_name", "squad_workspace"))
    if not indexer.is_available():
        return ""

    # Agent-specific queries
    queries = _get_queries_for_agent(agent_name, task)
    results = []
    for q in queries:
        try:
            items = indexer.query(q, n_results=3)
            results.extend(items)
        except Exception:
            pass

    if not results:
        return ""

    # Deduplicate by source file and line chunk to prevent overlap duplicates
    seen = set()
    unique = []
    for r in results:
        key = (r["source"], r["start_line"])
        if key not in seen:
            seen.add(key)
            unique.append(r)

    # Format as focused context
    formatted = []
    for r in unique[:10]:  # max 10 fragments
        formatted.append(f"--- {r['source']} (línea {r['start_line']}) ---\n{r['document'][:800]}")

    if not formatted:
        return ""

    header = f"## FRAGMENTOS RELEVANTES (RAG — top {len(formatted)} resultados)\n\n"
    return header + "\n\n".join(formatted)


def _get_queries_for_agent(agent_name: str, task: str) -> List[str]:
    """Generate search queries based on agent role and current task."""
    base = {
        "backend": ["API endpoints routes server logic", "database models queries SQLAlchemy"],
        "frontend": ["UI components HTML CSS React", "frontend rendering templates"],
        "qa": ["test assertions validation error handling", "test coverage unit tests"],
        "review": ["code quality patterns best practices", "security vulnerabilities validation"],
        "fix": ["error traceback bug fix", "failed test assertion fix patch"],
        "devops": ["deployment configuration Dockerfile", "build scripts requirements"],
    }
    agent_queries = list(base.get(agent_name.lower(), ["code implementation"]))
    if task:
        agent_queries.insert(0, task[:200])  # primary query
    return agent_queries
