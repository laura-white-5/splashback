""" Skills Framework module

Responsibility: the skills at each level and each child's status for each skill.
Prototype label: SIMPLIFIED - one level's skills and statuses loaded from a
JSON data file. In the target design, statuses could be imported from a coach portal.
"""

import json
from dataclasses import dataclass
from pathlib import Path

DEFAULT_DATA = Path(__file__).resolve().parent.parent / "data" / "skills.json"

ACHIEVED = "achieved"
IN_PROGRESS = "in_progress"
NOT_YET = "not_yet"
VALID_STATUSES = {ACHIEVED, IN_PROGRESS, NOT_YET}


@dataclass
class SkillStatus:
    skill_id: str
    name: str
    status: str


class SkillsService:
    # Interface: get_statuses(child_id) -> list[SkillStatus]

    def __init__(self, data_path=DEFAULT_DATA):
        with open(data_path, encoding="utf-8") as f:
            data = json.load(f)
        self._levels = data["levels"]
        self._statuses = data["statuses"]
        self._skill_names = {
            s["skill_id"]: s["name"] for skills in self._levels.values() for s in skills
        }

    def get_skills(self, level):
        # Return the skills for a level, e.g. get_skills(3)
        return list(self._levels.get(str(level), []))

    def get_statuses(self, child_id):
        if child_id not in self._statuses:
            raise KeyError(f"Unknown child: {child_id}")
        return [
            SkillStatus(skill_id=skill_id, name=self._skill_names[skill_id], status=status)
            for skill_id, status in self._statuses[child_id].items()
        ]