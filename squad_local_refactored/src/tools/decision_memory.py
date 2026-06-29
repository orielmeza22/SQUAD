import os
import json
from typing import Dict, Any, List, Optional


class DecisionMemory:
    def __init__(self, workspace: str):
        self.workspace = workspace
        self.filepath = os.path.join(workspace, ".squad_state", "decision_memory.json")
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        self.memory: Dict[str, str] = self._load()

    def _load(self) -> Dict[str, str]:
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save(self):
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.memory, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def add_decision(self, key: str, decision: str):
        self.memory[key.lower().strip()] = decision.strip()
        self._save()

    def get_decision(self, key: str) -> Optional[str]:
        return self.memory.get(key.lower().strip())

    def clear(self):
        self.memory.clear()
        self._save()


class AssumptionsLedger:
    def __init__(self, workspace: str):
        self.workspace = workspace
        self.filepath = os.path.join(workspace, ".squad_state", "assumptions_ledger.json")
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        self.ledger: Dict[str, Dict[str, Any]] = self._load()

    def _load(self) -> Dict[str, Dict[str, Any]]:
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save(self):
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.ledger, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def register_assumption(self, id: str, title: str, details: str):
        self.ledger[id] = {
            "id": id,
            "title": title,
            "details": details,
            "resolved_value": None,
            "status": "pending"
        }
        self._save()

    def resolve_assumption(self, id: str, resolved_value: str, status: str = "approved"):
        if id in self.ledger:
            self.ledger[id]["resolved_value"] = resolved_value
            self.ledger[id]["status"] = status
            self._save()

    def get_all(self) -> List[Dict[str, Any]]:
        return list(self.ledger.values())
