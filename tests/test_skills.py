import pytest
from skills.service import SkillsService, ACHIEVED, IN_PROGRESS, NOT_YET, VALID_STATUSES


def test_returns_correct_statuses_for_liam():
    skills = SkillsService()
    statuses = {s.skill_id: s.status for s in skills.get_statuses("C4")}
    assert statuses["L3-1"] == ACHIEVED      # first skill
    assert statuses["L3-2"] == IN_PROGRESS   # second skill
    assert statuses["L3-3"] == NOT_YET       # third skill

def test_unknown_child_raises_error():
    skills = SkillsService()
    with pytest.raises(KeyError):
        skills.get_statuses("NO-SUCH-CHILD")


def test_level_3_has_five_skills():
    assert len(SkillsService().get_skills(3)) == 5


def test_all_statuses_in_data_are_valid():
    skills = SkillsService()
    for child_id in ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"]:
        for s in skills.get_statuses(child_id):
            assert s.status in VALID_STATUSES