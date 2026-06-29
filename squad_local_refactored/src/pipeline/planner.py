from typing import List, Dict
import json
import re
from pydantic import BaseModel, Field


class Subtask(BaseModel):
    id: str
    name: str
    dependencies: List[str] = Field(default_factory=list)
    agent_role: str  # "dba" | "backend" | "frontend" | "qa"
    description: str
    budget_iterations: int = 15
    budget_tokens: int = 200000


class DAGPlanner:
    @staticmethod
    def topological_sort(subtasks: List[Subtask]) -> List[Subtask]:
        # Build dependency graph
        graph: Dict[str, List[str]] = {task.id: [] for task in subtasks}
        in_degree: Dict[str, int] = {task.id: 0 for task in subtasks}
        task_map: Dict[str, Subtask] = {task.id: task for task in subtasks}

        for task in subtasks:
            for dep in task.dependencies:
                if dep in graph:
                    graph[dep].append(task.id)
                    in_degree[task.id] += 1

        # Kahn's algorithm for topological sorting
        queue = [task_id for task_id, deg in in_degree.items() if deg == 0]
        sorted_tasks = []

        while queue:
            # Deterministic sorting of node IDs
            queue.sort()
            curr = queue.pop(0)
            sorted_tasks.append(task_map[curr])

            for neighbor in graph[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(sorted_tasks) != len(subtasks):
            raise ValueError(
                "Ciclo detectado en las dependencias del plan. "
                "La planificación debe ser un Grafo Acíclico Dirigido (DAG)."
            )

        return sorted_tasks

    @classmethod
    def parse_llm_plan(cls, raw_response: str) -> List[Subtask]:
        """
        Parses LLM planner output.
        Falls back to a default sequential DAG if parsing fails.
        """
        try:
            # Search for JSON array block
            json_match = re.search(r"\[\s*\{.*\}\s*\]", raw_response, re.DOTALL)
            if json_match:
                tasks_data = json.loads(json_match.group(0))
                subtasks = []
                for item in tasks_data:
                    subtasks.append(Subtask(
                        id=str(item.get("id")),
                        name=str(item.get("name")),
                        dependencies=list(item.get("dependencies", [])),
                        agent_role=str(item.get("agent_role")).lower(),
                        description=str(item.get("description")),
                        budget_iterations=int(item.get("budget_iterations", 15)),
                        budget_tokens=int(item.get("budget_tokens", 200000))
                    ))
                return subtasks
        except Exception:
            pass

        # Fallback sequential DAG default pipeline
        return [
            Subtask(id="task_dba", name="Esquema Base de Datos", dependencies=[], agent_role="dba", description="Generar y verificar bases de datos físicas en local."),
            Subtask(id="task_backend", name="Controladores y Endpoints", dependencies=["task_dba"], agent_role="backend", description="Construir controladores y API endpoints."),
            Subtask(id="task_frontend", name="Interfaz de Usuario", dependencies=["task_backend"], agent_role="frontend", description="Escribir frontend HTML/CSS/JS e integración."),
            Subtask(id="task_qa", name="Verificación QA", dependencies=["task_frontend"], agent_role="qa", description="Generar tests e inyectar validaciones.")
        ]
