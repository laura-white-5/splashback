# A pretend AI that follows those rules, so we can test without a real one
"""Mock AI provider.

Prototype label: the real LLM is replaced by a predictable mock in
Deliverable 2. It builds a draft directly from the skill statuses and note,
so tests always get the same result. It can also simulate an outage, or add
an unsupported claim, to test how the rest of the system reacts.
"""
from ai_provider.base import AIProvider, AIServiceUnavailable, DraftItem, DraftReport


class MockAIProvider(AIProvider):
    def __init__(self, fail=False, extra_claim=None):
        self.fail = fail                # True = simulate the AI service being down
        self.extra_claim = extra_claim  # e.g. "Just started inverted breaststroke"

    def generate(self, context):
        if self.fail:
            raise AIServiceUnavailable("Mock AI service is down")

        draft = DraftReport()
        for s in context.statuses:
            if s.status == "achieved":
                draft.doing_well.append(DraftItem(f"Good progress: {s.name.lower()}", s.skill_id, "skill"))
            elif s.status == "in_progress":
                draft.working_on.append(DraftItem(f"Working on: {s.name.lower()}", s.skill_id, "skill"))
        draft.working_on.append(DraftItem(f"Teacher noted: {context.note_text}", None, "note"))

        in_progress = [s for s in context.statuses if s.status == "in_progress"]
        if in_progress:
            draft.practise_next.append(
                DraftItem(f"Practise {in_progress[0].name.lower()}", in_progress[0].skill_id, "skill"))

        if self.extra_claim:
            draft.working_on.append(DraftItem(self.extra_claim, None, "note"))
        return draft