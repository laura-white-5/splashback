"""End-to-end tests of the chosen feature through the web pages (scenario tests)."""
import pytest
from app import create_app

CLASS = "L3-SAT-0940"


@pytest.fixture
def client(tmp_path):
    app = create_app(db_path=tmp_path / "test.db")
    app.config["TESTING"] = True
    return app.test_client()


def test_home_page_lists_class(client):
    assert b"Level 3" in client.get("/").data


def test_full_workflow_note_generate_review_approve(client):
    # S1 + S2: enter a note, generate, open the report, approve it
    client.post(f"/class/{CLASS}/notes/3", data={"note": "bent knees when kick on back", "action": "done"})
    client.post(f"/class/{CLASS}/generate", data={})
    assert b"Review report" in client.get(f"/class/{CLASS}/review/C4").data   # opening marks it as read
    response = client.post(f"/class/{CLASS}/review/C4", data={"action": "approve"})
    assert response.status_code == 302                                          # redirected to approved page
    assert b"Drafted with AI" in client.get(f"/class/{CLASS}/approved/C4").data


def test_ai_outage_shows_message_and_keeps_note(client):
    # S4
    client.post(f"/class/{CLASS}/notes/3", data={"note": "bent knees", "action": "done"})
    page = client.post(f"/class/{CLASS}/generate", data={"outage": "on"}).data
    assert b"unavailable" in page
    assert b"bent knees" in client.get(f"/class/{CLASS}/notes/3").data


def test_ai_mistake_is_flagged_and_blocks_approval(client):
    # S5
    client.post(f"/class/{CLASS}/notes/3", data={"note": "bent knees when kick on back", "action": "done"})
    client.post(f"/class/{CLASS}/generate", data={"mistake": "on"})
    page = client.get(f"/class/{CLASS}/review/C4").data
    assert b"inverted breaststroke" in page
    response = client.post(f"/class/{CLASS}/review/C4", data={"action": "approve"})
    assert b"Resolve all warnings" in response.data


def test_empty_note_shows_error(client):
    page = client.post(f"/class/{CLASS}/notes/0", data={"note": "  ", "action": "done"}).data
    assert b"cannot be empty" in page