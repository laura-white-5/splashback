"""Report Generation, step 3: check the AI's draft before a teacher sees it

Safety mitigation (risk register): a draft must never claim a skill the child
has not achieved, and every other claim must be supported by the teacher's note
"""
import string
from dataclasses import dataclass

STOPWORDS = {"the", "and", "with", "when", "his", "her", "their", "on", "in", "of",
             "to", "a", "is", "was", "just", "very", "good", "great", "teacher", "noted",
             "swimmer", "working", "progress", "practise", "started"}


@dataclass
class DraftWarning:
    item_text: str
    reason: str


def _keywords(text):
    words = set()
    for w in text.lower().split():      # split on spaces
        w = w.strip(string.punctuation) # removes commas, full stops etc. from the ends
        if len(w) > 2 and w not in STOPWORDS:
            words.add(w)
    return words


def check_draft(draft, statuses, note_text):
    # Return a list of warnings. An empty list means the draft passed
    status_by_id = {s.skill_id: s.status for s in statuses}
    note_words = _keywords(note_text)
    warnings = []

    # Rule 1: "Doing well" may only mention achieved skills
    for item in draft.doing_well:
        if item.skill_id and status_by_id.get(item.skill_id) != "achieved":
            warnings.append(DraftWarning(item.text, "Claims a skill the child has not achieved"))

    for item in draft.all_items():
        # Rule 2: a line about a skill must be about one of this child's skills
        if item.skill_id and item.skill_id not in status_by_id:
            warnings.append(DraftWarning(item.text, "Mentions a skill not in this child's level"))
        # Rule 3: a line not about a skill must be supported by the teacher's note
        elif not item.skill_id and not (_keywords(item.text) & note_words):
            warnings.append(DraftWarning(item.text, "Not found in the teacher's note or skills"))

    return warnings