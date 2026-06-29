import os
import shutil
import pytest
from squad_local_refactored.src.tools.decision_memory import DecisionMemory, AssumptionsLedger
from squad_local_refactored.src.tools.test_consensus import TestConsensusValidator


@pytest.fixture
def temp_workspace(tmp_path):
    workspace_dir = tmp_path / "fase4_workspace"
    workspace_dir.mkdir()
    yield str(workspace_dir)
    shutil.rmtree(workspace_dir, ignore_errors=True)


def test_test_consensus_validation():
    # 1. Valid test code
    valid_test = """
def test_addition():
    assert 1 + 1 == 2
"""
    success, msg = TestConsensusValidator.validate_test_code(valid_test)
    assert success is True
    assert msg == ""

    # 2. Syntax error
    invalid_test = """
def test_addition()
    assert 1 + 1 == 2
"""
    success, msg = TestConsensusValidator.validate_test_code(invalid_test)
    assert success is False
    assert "Error de sintaxis" in msg

    # 3. No test function
    no_test_func = """
def helper_func():
    assert True
"""
    success, msg = TestConsensusValidator.validate_test_code(no_test_func)
    assert success is False
    assert "no define ninguna función" in msg

    # 4. No assertions
    no_assertions = """
def test_do_nothing():
    x = 10
"""
    success, msg = TestConsensusValidator.validate_test_code(no_assertions)
    assert success is False
    assert "no contiene sentencias 'assert'" in msg


def test_decision_memory_persistence(temp_workspace):
    memory = DecisionMemory(temp_workspace)
    memory.add_decision("auth", "JWT")
    memory.add_decision("db_provider", "PostgreSQL")

    # Verify retrieval
    assert memory.get_decision("auth") == "JWT"
    assert memory.get_decision("DB_PROVIDER") == "PostgreSQL"
    
    # Reload and test persistence
    new_memory = DecisionMemory(temp_workspace)
    assert new_memory.get_decision("auth") == "JWT"
    assert new_memory.get_decision("db_provider") == "PostgreSQL"


def test_assumptions_ledger(temp_workspace):
    ledger = AssumptionsLedger(temp_workspace)
    ledger.register_assumption("asm_1", "Single-tenant", "Assumed the application runs in single-tenant mode.")
    
    assumptions = ledger.get_all()
    assert len(assumptions) == 1
    assert assumptions[0]["id"] == "asm_1"
    assert assumptions[0]["status"] == "pending"

    # Resolve it
    ledger.resolve_assumption("asm_1", "Multi-tenant", "approved")
    
    updated = ledger.get_all()
    assert updated[0]["status"] == "approved"
    assert updated[0]["resolved_value"] == "Multi-tenant"
