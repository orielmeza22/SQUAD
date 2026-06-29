import pytest
from squad_local_refactored.src.pipeline.planner import DAGPlanner, Subtask


def test_topological_sort_success():
    # A -> B -> C, and A -> C
    tasks = [
        Subtask(id="C", name="Task C", dependencies=["B", "A"], agent_role="frontend", description="..."),
        Subtask(id="A", name="Task A", dependencies=[], agent_role="dba", description="..."),
        Subtask(id="B", name="Task B", dependencies=["A"], agent_role="backend", description="..."),
    ]
    sorted_tasks = DAGPlanner.topological_sort(tasks)
    
    # Must be A, then B, then C
    assert [t.id for t in sorted_tasks] == ["A", "B", "C"]


def test_topological_sort_cycle():
    # A -> B -> A
    tasks = [
        Subtask(id="A", name="Task A", dependencies=["B"], agent_role="dba", description="..."),
        Subtask(id="B", name="Task B", dependencies=["A"], agent_role="backend", description="..."),
    ]
    with pytest.raises(ValueError, match="Ciclo detectado"):
        DAGPlanner.topological_sort(tasks)


def test_parse_llm_plan_json():
    raw_response = """
Here is the plan:
[
  {
    "id": "t1",
    "name": "DB init",
    "dependencies": [],
    "agent_role": "dba",
    "description": "Init db schema",
    "budget_iterations": 10,
    "budget_tokens": 150000
  },
  {
    "id": "t2",
    "name": "API build",
    "dependencies": ["t1"],
    "agent_role": "backend",
    "description": "API endpoints",
    "budget_iterations": 20,
    "budget_tokens": 300000
  }
]
Hope it works!
"""
    tasks = DAGPlanner.parse_llm_plan(raw_response)
    assert len(tasks) == 2
    assert tasks[0].id == "t1"
    assert tasks[1].id == "t2"
    assert tasks[1].dependencies == ["t1"]


def test_parse_llm_plan_fallback():
    raw_response = "I cannot generate a plan. Error 500."
    tasks = DAGPlanner.parse_llm_plan(raw_response)
    # Falls back to default pipeline: dba -> backend -> frontend -> qa
    assert len(tasks) == 4
    assert [t.agent_role for t in tasks] == ["dba", "backend", "frontend", "qa"]
