"""Unit tests for SysTools."""

import os
import shutil
import pytest
from src.tools.sys_tools import SysTools, sanitize_workspace_path


@pytest.fixture(autouse=True)
def setup_test_workspace():
    test_workspace = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_workspace_tools"))
    os.makedirs(test_workspace, exist_ok=True)
    SysTools.WORKSPACE = test_workspace
    yield
    shutil.rmtree(test_workspace, ignore_errors=True)


def test_sanitize_workspace_path():
    path = sanitize_workspace_path("subfolder/file.txt")
    assert path.startswith(SysTools.WORKSPACE)
    assert path.endswith(os.path.normpath("subfolder/file.txt"))


def test_write_and_read():
    filename = "test_file.txt"
    content = "Hello SQUAD Refactored!"
    
    # Write file
    path = SysTools.write(filename, content, force=True)
    assert os.path.exists(path)
    
    # Read file
    read_content = SysTools.read(filename)
    assert read_content == content


def test_cleanup_workspace_processes():
    # Verify cleanup runs without crashing
    SysTools.cleanup_workspace_processes()


def test_extract_multifile_in_memory_json():
    json_output = """
    ```json
    [
      {
        "tool": "write_file",
        "parameters": {
          "path": "app.py",
          "content": "print('hello')"
        }
      }
    ]
    ```
    """
    files = SysTools.extract_multifile_in_memory(json_output)
    assert "app.py" in files
    assert files["app.py"] == "print('hello')"

