import os
import pytest
from squad_local_refactored.src.tools.action_executor import ActionExecutor, ToolCall, ToolResult
from squad_local_refactored.src.tools.sys_tools import SysTools

def test_action_executor_write_file(tmp_path):
    # Set workspace to a temporary directory
    original_workspace = SysTools.WORKSPACE
    SysTools.WORKSPACE = str(tmp_path)
    
    try:
        executor = ActionExecutor()
        llm_output = """
        [
            {
                "tool": "write_file",
                "parameters": {
                    "path": "test_json.py",
                    "content": "print('Hello JSON')"
                }
            }
        ]
        """
        calls = executor.parse(llm_output)
        assert len(calls) == 1
        assert calls[0].tool == "write_file"
        assert calls[0].parameters["path"] == "test_json.py"
        
        results = executor.execute_all(llm_output)
        assert len(results) == 1
        assert results[0].success is True
        
        # Verify file exists on disk
        target_file = tmp_path / "test_json.py"
        assert target_file.exists()
        assert target_file.read_text(encoding="utf-8") == "print('Hello JSON')"
    finally:
        SysTools.WORKSPACE = original_workspace

def test_action_executor_path_traversal(tmp_path):
    original_workspace = SysTools.WORKSPACE
    SysTools.WORKSPACE = str(tmp_path)
    
    try:
        executor = ActionExecutor()
        llm_output = """
        [
            {
                "tool": "write_file",
                "parameters": {
                    "path": "../escape.txt",
                    "content": "malicious"
                }
            }
        ]
        """
        results = executor.execute_all(llm_output)
        assert len(results) == 1
        assert results[0].success is False
        assert "SecurityError" in results[0].message
        
        # Verify it wasn't written
        target = tmp_path.parent / "escape.txt"
        assert not target.exists()
    finally:
        SysTools.WORKSPACE = original_workspace

def test_action_executor_legacy_fallback(tmp_path):
    original_workspace = SysTools.WORKSPACE
    SysTools.WORKSPACE = str(tmp_path)
    
    try:
        executor = ActionExecutor()
        # Legacy @@FILE syntax
        llm_output = "@@FILE:app_legacy.py\nprint('Legacy content')\n@@ENDFILE@@"
        
        results = executor.execute_all(llm_output)
        assert len(results) == 1
        assert results[0].success is True
        assert "legacy_fallback" in results[0].tool
        
        target = tmp_path / "app_legacy.py"
        assert target.exists()
        # Cleaned by legacy extractor
        assert "print('Legacy content')" in target.read_text(encoding="utf-8")
    finally:
        SysTools.WORKSPACE = original_workspace

def test_action_executor_malformed_json():
    executor = ActionExecutor()
    llm_output = """
    [
        {
            "tool": "write_file",
            "parameters": {
                "path": "test.py",
                "content": "unclosed string
    """
    calls = executor.parse(llm_output)
    # Malformed JSON should not raise exceptions but return empty or fall back
    assert isinstance(calls, list)

def test_action_executor_execute_cmd_blocked():
    executor = ActionExecutor()
    llm_output = """
    [
        {
            "tool": "execute_cmd",
            "parameters": {
                "cmd": "rm -rf /"
            }
        }
    ]
    """
    results = executor.execute_all(llm_output)
    assert len(results) == 1
    assert results[0].success is False
    assert "SecurityError" in results[0].message

