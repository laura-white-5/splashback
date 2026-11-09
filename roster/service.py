""" Classes & Roster module

Responsibility: schools, classes and the children in each class.
Prototype label: SIMPLIFIED - one class loaded from a JSON data file
instead of a database.
"""

import json
from dataclasses import dataclass
from pathlib import Path

DEFAULT_DATA = Path(__file__).resolve().parent.parent / "data" / "roster.json"


@dataclass
class Child:
    child_id: str
    name: str


@dataclass
class SwimClass:
    class_id: str
    level: int
    day: str
    time: str
    teacher_id: str
    children: list


class RosterService:
    """Interface: get_class(class_id) -> SwimClass"""

    def __init__(self, data_path=DEFAULT_DATA):
        with open(data_path, encoding="utf-8") as f:
            data = json.load(f)
        self._classes = {}
        for c in data["classes"]:
            children = [Child(**child) for child in c["children"]]
            self._classes[c["class_id"]] = SwimClass(
                class_id=c["class_id"], level=c["level"], day=c["day"],
                time=c["time"], teacher_id=c["teacher_id"], children=children,
            )

    def get_class(self, class_id):
        if class_id not in self._classes:
            raise KeyError(f"Unknown class: {class_id}")
        return self._classes[class_id]

    def get_classes_for_teacher(self, teacher_id):
        return [c for c in self._classes.values() if c.teacher_id == teacher_id]