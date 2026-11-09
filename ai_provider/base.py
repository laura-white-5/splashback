# Rules any AI must follow
"""AI Provider interface.

Every AI provider (the mock now, a real LLM in Deliverable 3) must implement
generate(context) -> DraftReport. The rest of the system only ever uses this
interface, so swapping providers does not change any other code.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


class AIServiceUnavailable(Exception):
    """Raised when the AI service cannot be reached or does not respond."""


@dataclass
class DraftItem:
    text: str
    skill_id: str = None   # which skill this line is about, if any
    source: str = "note"   # "skill" or "note": where the claim comes from


@dataclass
class DraftReport:
    doing_well: list = field(default_factory=list)
    working_on: list = field(default_factory=list)
    practise_next: list = field(default_factory=list)

    def all_items(self):
        return self.doing_well + self.working_on + self.practise_next


class AIProvider(ABC):
    @abstractmethod
    def generate(self, context):
        """Take a ReportContext and return a DraftReport."""