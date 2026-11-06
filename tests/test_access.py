from access.service import AccessService
from roster.service import RosterService


def test_demo_teacher_can_view_child_in_their_class():
    access = AccessService(RosterService())
    assert access.can_view("T1", "C4") is True


def test_other_user_cannot_view_child():
    access = AccessService(RosterService())
    assert access.can_view("PARENT-99", "C4") is False


def test_teacher_cannot_view_child_not_in_their_class():
    access = AccessService(RosterService())
    assert access.can_view("T1", "C999") is False