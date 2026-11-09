import pytest
from ai_provider.base import AIProvider, AIServiceUnavailable
from ai_provider.factory import get_ai_provider
from ai_provider.mock import MockAIProvider
from reports.context import ReportContext
from skills.service import SkillsService


def make_context():
    return ReportContext(level=3, statuses=SkillsService().get_statuses("C4"),
                         note_text="bent knees when kick on back")


def test_factory_returns_an_ai_provider():
    assert isinstance(get_ai_provider(), AIProvider)


def test_mock_returns_all_three_sections():
    draft = MockAIProvider().generate(make_context())
    assert draft.doing_well and draft.working_on and draft.practise_next


def test_mock_can_simulate_outage():
    with pytest.raises(AIServiceUnavailable):
        MockAIProvider(fail=True).generate(make_context())