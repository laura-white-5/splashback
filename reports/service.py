"""Report Generation module.

Responsibility: turn teachers' notes into checked draft reports.
Pipeline: build context -> generate draft (via AIProvider) -> check draft.
Prototype label: BUILT - same three steps as the target design but called
directly instead of through a message queue (SIMPLIFIED queue, see deviation log).
Uses other modules only through their interfaces.
"""
from ai_provider.base import AIServiceUnavailable
from reports.check import check_draft
from reports.context import build_context
import time

class ReportService:
    # Interface: request_reports(class_id, lesson_id) -> summary dict

    def __init__(self, roster, skills, notes, review, ai_provider, retries=1, retry_delay=0):
        self._roster = roster
        self._skills = skills
        self._notes = notes
        self._review = review
        self._ai = ai_provider
        self._retries = retries
        self._retry_delay = retry_delay

    def _generate_with_retry(self, context):
        for attempt in range(self._retries + 1):
            try:
                return self._ai.generate(context)
            except AIServiceUnavailable:
                if attempt == self._retries:
                    raise
                time.sleep(self._retry_delay)  # give a busy service a moment before retrying
        raise AIServiceUnavailable("AI unavailable after all retries")

    def request_reports(self, class_id, lesson_id):
        swim_class = self._roster.get_class(class_id)
        summary = {"drafted": [], "no_notes": [], "ai_unavailable": [], "already_approved": []}
        for child in swim_class.children:
            # Never overwrite a report the teacher has already approved (risk N2).
            existing = self._review.get_report(child.child_id, lesson_id)
            if existing and existing["status"] == "approved":
                summary["already_approved"].append(child.child_id)
                continue
            note = self._notes.get_note(child.child_id, lesson_id)
            if note is None:
                summary["no_notes"].append(child.child_id)
                continue

            statuses = self._skills.get_statuses(child.child_id)
            context = build_context(child, swim_class.level, statuses, note.text)   # step 1
            try:
                draft = self._generate_with_retry(context)                           # step 2
            except AIServiceUnavailable:
                # Resilience: the note is already saved, so nothing is lost.
                summary["ai_unavailable"].append(child.child_id)
                continue
            warnings = check_draft(draft, statuses, context.note_text)               # step 3
            self._review.submit_draft(child.child_id, lesson_id, draft, warnings)
            summary["drafted"].append(child.child_id)

        return summary

    def recheck(self, child_id, lesson_id, draft):
        # Re-run the check after a teacher edits a draft.
        statuses = self._skills.get_statuses(child_id)
        note = self._notes.get_note(child_id, lesson_id)
        return check_draft(draft, statuses, note.text if note else "")