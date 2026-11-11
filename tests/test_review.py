import pytest
from ai_provider.base import DraftItem, DraftReport
from reports.check import DraftWarning
from review.service import ApprovalError, ReviewService

GOOD_DRAFT = DraftReport(doing_well=[DraftItem("Strong front kick", "L3-1", "skill")])


@pytest.fixture
def review(tmp_path):
    return ReviewService(tmp_path / "test.db")


def submit(review, warnings=()):
    review.submit_draft("C4", "LESSON-1", GOOD_DRAFT, list(warnings))
    return review.get_report("C4", "LESSON-1")["report_id"]


def test_report_is_not_shareable_until_approved(review):
    report_id = submit(review)
    assert review.is_shareable(report_id) is False


def test_cannot_approve_without_opening(review):
    report_id = submit(review)
    with pytest.raises(ApprovalError):
        review.approve(report_id, "T1")


def test_cannot_approve_with_unresolved_warnings(review):
    report_id = submit(review, [DraftWarning("Just started inverted breaststroke", "Not found")])
    review.mark_opened(report_id)
    with pytest.raises(ApprovalError):
        review.approve(report_id, "T1")


def test_approval_records_teacher_and_time(review):
    report_id = submit(review)
    review.mark_opened(report_id)
    review.approve(report_id, "T1")
    report = review.get_report("C4", "LESSON-1")
    assert report["status"] == "approved"
    assert report["approved_by"] == "T1"
    assert report["approved_at"] is not None
    assert review.is_shareable(report_id) is True


def test_editing_out_the_warning_allows_approval(review):
    report_id = submit(review, [DraftWarning("Just started inverted breaststroke", "Not found")])
    review.mark_opened(report_id)
    review.update_draft(report_id, GOOD_DRAFT, warnings=[])  # teacher removed the bad line
    review.approve(report_id, "T1")
    assert review.is_shareable(report_id) is True