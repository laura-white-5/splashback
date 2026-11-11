import pytest
from ai_provider.mock import MockAIProvider
from notes.service import NotesService
from reports.service import ReportService
from review.service import ReviewService
from roster.service import RosterService
from skills.service import SkillsService

CLASS_ID = "L3-SAT-0940"
LESSON = "LESSON-1"


@pytest.fixture
def setup(tmp_path):
    db = tmp_path / "test.db"
    notes, review = NotesService(db), ReviewService(db)

    def make_service(ai):
        return ReportService(RosterService(), SkillsService(), notes, review, ai)
    return notes, review, make_service


def test_drafts_created_only_for_children_with_notes(setup):
    notes, review, make_service = setup
    notes.save_note("C4", LESSON, "bent knees when kick on back")
    notes.save_note("C1", LESSON, "lovely streamline today")
    summary = make_service(MockAIProvider()).request_reports(CLASS_ID, LESSON)
    assert sorted(summary["drafted"]) == ["C1", "C4"]
    assert len(summary["no_notes"]) == 6
    assert review.get_report("C4", LESSON) is not None


def test_ai_outage_keeps_notes_and_creates_no_draft(setup):
    notes, review, make_service = setup
    notes.save_note("C4", LESSON, "bent knees when kick on back")
    summary = make_service(MockAIProvider(fail=True)).request_reports(CLASS_ID, LESSON)
    assert summary["ai_unavailable"] == ["C4"]
    assert review.get_report("C4", LESSON) is None
    assert notes.get_note("C4", LESSON).text == "bent knees when kick on back"  # nothing lost


def test_unsupported_claim_reaches_review_with_warning(setup):
    notes, review, make_service = setup
    notes.save_note("C4", LESSON, "bent knees when kick on back, nervous of deep water")
    ai = MockAIProvider(extra_claim="Just started inverted breaststroke")
    make_service(ai).request_reports(CLASS_ID, LESSON)
    report = review.get_report("C4", LESSON)
    assert len(report["warnings"]) == 1

def test_generating_again_does_not_overwrite_approved_report(setup):
    notes, review, make_service = setup
    notes.save_note("C4", LESSON, "bent knees when kick on back")
    service = make_service(MockAIProvider())
    service.request_reports(CLASS_ID, LESSON)
    report_id = review.get_report("C4", LESSON)["report_id"]
    review.mark_opened(report_id)
    review.approve(report_id, "T1")

    summary = service.request_reports(CLASS_ID, LESSON)   # teacher clicks Generate again
    assert summary["already_approved"] == ["C4"]
    assert review.get_report("C4", LESSON)["status"] == "approved"