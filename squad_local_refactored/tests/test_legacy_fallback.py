import os
import shutil
import pytest
from squad_local_refactored.src.tools.sys_tools import SysTools
from squad_local_refactored.src.tools.action_executor import ActionExecutor


@pytest.fixture
def temp_workspace(tmp_path):
    orig_workspace = SysTools.WORKSPACE
    workspace_path = os.path.abspath(tmp_path / "legacy_test_workspace")
    os.makedirs(workspace_path, exist_ok=True)
    SysTools.WORKSPACE = workspace_path
    yield workspace_path
    shutil.rmtree(workspace_path, ignore_errors=True)
    SysTools.WORKSPACE = orig_workspace


def test_legacy_fallback_extraction_and_write(temp_workspace):
    legacy_output = """
@@FILE: test_legacy.txt
Hello Legacy World!
This is a file written using legacy batch format tags.
@@ENDFILE@@
"""
    # 1. Verify parser extracts it as legacy_fallback ToolCall
    executor = ActionExecutor()
    calls = executor.parse(legacy_output)
    assert len(calls) == 1
    assert calls[0].tool == "legacy_fallback"
    assert "test_legacy.txt" in calls[0].parameters.get("files", [])

    # 2. Verify SysTools.extract_and_write_multifile successfully writes and registers the file
    modified_files = SysTools.extract_and_write_multifile(legacy_output)
    assert "test_legacy.txt" in modified_files

    # 3. Verify physical file exists and has correct content
    file_path = os.path.join(temp_workspace, "test_legacy.txt")
    assert os.path.exists(file_path)
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Hello Legacy World!" in content
