import pytest
from roster.service import RosterService


def test_get_class_returns_eight_children():
    roster = RosterService()
    swim_class = roster.get_class("L3-SAT-0940")
    assert swim_class.level == 3
    assert len(swim_class.children) == 8


def test_unknown_class_raises_error():
    roster = RosterService()
    with pytest.raises(KeyError):
        roster.get_class("NOT-A-CLASS")


def test_teacher_sees_only_their_classes():
    roster = RosterService()
    assert len(roster.get_classes_for_teacher("T1")) == 4
    assert roster.get_classes_for_teacher("SOMEONE-ELSE") == []

