import os
import json
from typing import Dict, Any


class UserProfileManager:
    def __init__(self, workspace: str):
        self.workspace = workspace
        self.filepath = os.path.join(workspace, ".squad_state", "user_profile.json")
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        self.profile = self._load()

    def _load(self) -> Dict[str, Any]:
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        # Default user preferences
        return {
            "naming_convention": "snake_case",
            "typescript_strict": True,
            "styling_framework": "tailwind",
            "test_runner": "pytest",
            "preferred_libraries": []
        }

    def _save(self):
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.profile, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def get_preference(self, key: str, default: Any = None) -> Any:
        return self.profile.get(key, default)

    def set_preference(self, key: str, value: Any):
        self.profile[key] = value
        self._save()
