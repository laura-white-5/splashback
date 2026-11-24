"""Report Generation, step 1: build the context sent to the AI.

Privacy mitigation (risk register): the child's real name is replaced with a
placeholder before anything is sent to the AI provider.
"""
from dataclasses import dataclass

PLACEHOLDER = "the swimmer"


@dataclass
class ReportContext:
    level: int
    statuses: list      # list of SkillStatus
    note_text: str      # teacher's note with the child's name removed


def remove_name(text, full_name):
    # Replace the child's full name and first name with a placeholder.
    first_name = full_name.split()[0]
    for name in (full_name, first_name):
        text = text.replace(name, PLACEHOLDER)
    return text


def build_context(child, level, statuses, note_text):
    return ReportContext(level=level, statuses=statuses,
                         note_text=remove_name(note_text, child.name))

def restore_name(draft, full_name):
    # Put the child's first name back into the draft after the AI and the check have finished, so the parent's report reads naturally (the AI never saw the name)
    first_name = full_name.split()[0]
    for item in draft.all_items():
        item.text = item.text.replace("The swimmer", first_name).replace("the swimmer", first_name)
    return draft