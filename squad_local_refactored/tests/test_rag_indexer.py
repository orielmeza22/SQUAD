import os
import json
import pytest
from squad_local_refactored.src.core.config import settings
from squad_local_refactored.src.tools.rag_indexer import RAGIndexer, CHROMA_AVAILABLE
from squad_local_refactored.src.tools.context_enricher import enrich_context, _get_queries_for_agent
from squad_local_refactored.src.tools.sys_tools import SysTools
from squad_local_refactored.src.pipeline import graph_orchestrator as go


def test_chunk_content():
    indexer = RAGIndexer("./workspace")
    content = "line1\nline2\nline3\nline4\nline5\nline6\nline7\nline8"
    # Chunk size very small to force chunking
    chunks = indexer._chunk_content(content, "test.py", max_chars=12, overlap=5)
    assert len(chunks) > 1
    # Verify tuple values
    for chunk, start_line in chunks:
        assert isinstance(chunk, str)
        assert isinstance(start_line, int)


@pytest.mark.skipif(not CHROMA_AVAILABLE, reason="ChromaDB not installed")
def test_rag_indexer_flow(tmp_path):
    # Setup test workspace
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    
    # Create test files
    file1 = workspace / "app.py"
    file1.write_text("def main():\n    print('Hello World')\n", encoding="utf-8")
    
    file2 = workspace / "routes.py"
    file2.write_text("from fastapi import FastAPI\napp = FastAPI()\n", encoding="utf-8")

    indexer = RAGIndexer(str(workspace), "test_collection")
    assert indexer.is_available() is True

    # Test indexing
    stats = indexer.index_workspace()
    assert "app.py" in stats
    assert "routes.py" in stats
    
    # Test querying
    results = indexer.query("main print", n_results=1)
    assert len(results) > 0
    assert results[0]["source"] == "app.py"
    
    # Test clear
    indexer.clear()
    assert indexer._collection is None


@pytest.mark.skipif(not CHROMA_AVAILABLE, reason="ChromaDB not installed")
def test_context_enricher_disabled_and_enabled(monkeypatch, tmp_path):
    monkeypatch.setattr(SysTools, "WORKSPACE", str(tmp_path))
    
    # 1. RAG disabled by default
    monkeypatch.setattr(settings, "rag_enabled", False)
    ctx = enrich_context("backend", "API endpoints")
    assert ctx == ""
    
    # 2. RAG enabled
    monkeypatch.setattr(settings, "rag_enabled", True)
    monkeypatch.setattr(settings, "rag_collection_name", "test_enricher_col")
    
    # Index dummy file
    indexer = RAGIndexer(str(tmp_path), "test_enricher_col")
    indexer.index_file("backend.py", "def get_users(): return []\n", "python")
    
    ctx = enrich_context("backend", "get_users endpoint")
    assert "backend.py" in ctx
    assert "def get_users()" in ctx


def test_get_queries_for_agent():
    queries_backend = _get_queries_for_agent("backend", "create task table")
    assert "create task table" in queries_backend
    assert len(queries_backend) > 1

    queries_unknown = _get_queries_for_agent("unknown_agent", "")
    assert "code implementation" in queries_unknown


@pytest.mark.skipif(not CHROMA_AVAILABLE, reason="ChromaDB not installed")
def test_graph_nodes_rag_integration(monkeypatch, tmp_path):
    monkeypatch.setattr(SysTools, "WORKSPACE", str(tmp_path))
    monkeypatch.setattr(settings, "rag_enabled", True)
    monkeypatch.setattr(settings, "rag_collection_name", "test_graph_col")
    
    # Setup initial SPEC.md in workspace
    spec_path = tmp_path / "SPEC.md"
    spec_path.write_text("STACK: FASTAPI_HTMX\nAllowed files: main_output.py", encoding="utf-8")
    
    # Index SPEC.md
    indexer = RAGIndexer(str(tmp_path), "test_graph_col")
    indexer.index_file("SPEC.md", spec_path.read_text(encoding="utf-8"), "markdown")
    
    # Mock AIProvider.generate to check if RAG context is injected
    prompt_received = []
    
    def mock_generate(self, model, prompt, is_json=False):
        prompt_received.append(prompt)
        if "revisa los archivos creados" in prompt.lower():
            return "Veredicto: PASS"
        return "@@FILE: main_output.py\nprint('RAG Test')"

    monkeypatch.setattr("squad_local_refactored.src.llm.provider.AIProvider.generate", mock_generate)
    
    # Run a node to verify RAG enrichment
    state_val = {
        "prompt": "Build tasks app",
        "model": "gemini-2.5-flash",
        "target_model": "gemini-2.5-flash",
        "search_ctx": "",
        "plan": "STACK: FASTAPI_HTMX\nAllowed files: main_output.py",
        "stack": "FASTAPI_HTMX",
        "created_files": ["main_output.py"],
        "last_errors": [],
        "review_verdict": "PASS",
        "retries": {"backend": 0, "review": 0},
        "messages": []
    }
    
    # 1. Backend node
    go.node_backend(state_val)
    assert any("FRAGMENTOS RELEVANTES" in p for p in prompt_received)
    prompt_received.clear()
    
    # 2. Review node
    go.node_review(state_val)
    assert any("FRAGMENTOS DE CÓDIGO vs SPEC" in p for p in prompt_received)
