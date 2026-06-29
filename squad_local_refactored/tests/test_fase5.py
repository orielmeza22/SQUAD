import os
import shutil
import pytest
from squad_local_refactored.src.tools.user_profile import UserProfileManager
from squad_local_refactored.src.tools.mock_maker import MockMaker, ContractValidator
from squad_local_refactored.src.tools.rag_indexer import CHROMA_AVAILABLE


@pytest.fixture
def temp_workspace(tmp_path):
    workspace_dir = tmp_path / "fase5_workspace"
    workspace_dir.mkdir()
    yield str(workspace_dir)
    shutil.rmtree(workspace_dir, ignore_errors=True)


def test_user_profile_persistence(temp_workspace):
    manager = UserProfileManager(temp_workspace)
    
    # Verify defaults
    assert manager.get_preference("naming_convention") == "snake_case"
    assert manager.get_preference("typescript_strict") is True

    # Modify preferences
    manager.set_preference("naming_convention", "camelCase")
    manager.set_preference("styling_framework", "bootstrap")

    # Reload and test persistence
    new_manager = UserProfileManager(temp_workspace)
    assert new_manager.get_preference("naming_convention") == "camelCase"
    assert new_manager.get_preference("styling_framework") == "bootstrap"


def test_mock_maker_generation():
    schema = {
        "type": "object",
        "properties": {
            "id": {"type": "integer", "default": 1},
            "name": {"type": "string"},
            "is_active": {"type": "boolean", "default": False}
        }
    }
    
    mock = MockMaker.generate_mock_from_schema(schema)
    assert mock["id"] == 1
    assert mock["name"] == "mock_value"
    assert mock["is_active"] is False


def test_contract_validator():
    schema = {
        "required": ["id", "username"],
        "properties": {
            "id": {"type": "integer"},
            "username": {"type": "string"},
            "tags": {"type": "array"}
        }
    }

    # 1. Success case
    ok_payload = {"id": 42, "username": "alice", "tags": ["admin", "dev"]}
    success, msg = ContractValidator.validate_payload_against_schema(ok_payload, schema)
    assert success is True
    assert msg == ""

    # 2. Missing required field
    bad_payload1 = {"username": "bob"}
    success, msg = ContractValidator.validate_payload_against_schema(bad_payload1, schema)
    assert success is False
    assert "Falta el campo obligatorio" in msg

    # 3. Type mismatch
    bad_payload2 = {"id": "not_an_integer", "username": "bob"}
    success, msg = ContractValidator.validate_payload_against_schema(bad_payload2, schema)
    assert success is False
    assert "Tipo de dato incorrecto" in msg


@pytest.mark.skipif(not CHROMA_AVAILABLE, reason="ChromaDB not installed")
def test_skill_library_indexing(temp_workspace):
    from squad_local_refactored.src.tools.rag_indexer import RAGIndexer
    
    # Verify that RAGIndexer correctly runs and indexes workspace including skills
    indexer = RAGIndexer(temp_workspace, "test_skills_collection")
    stats = indexer.index_workspace()
    
    # "skills/sqlite_connection_singleton.py" should be found in indexed statistics if the folder exists
    skills_indexed = [k for k in stats.keys() if k.startswith("skills/")]
    assert len(skills_indexed) > 0
    assert "skills/sqlite_connection_singleton.py" in skills_indexed
