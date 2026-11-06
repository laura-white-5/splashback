import pytest
from notes.service import NotesService


@pytest.fixture
def notes(tmp_path):
    # Each test gets its own fresh, temporary database file.
    return NotesService(db_path=tmp_path / "test.db")


def test_note_is_saved_and_retrieved_for_correct_child(notes):
    notes.save_note("C4", "LESSON-1", "bent knees when kick on back")
    note = notes.get_note("C4", "LESSON-1")
    assert note.text == "bent knees when kick on back"
    assert notes.get_note("C1", "LESSON-1") is None


def test_empty_note_is_rejected(notes):
    with pytest.raises(ValueError):
        notes.save_note("C4", "LESSON-1", "   ")


def test_saving_again_replaces_the_note(notes):
    notes.save_note("C4", "LESSON-1", "first version")
    notes.save_note("C4", "LESSON-1", "second version")
    assert notes.get_note("C4", "LESSON-1").text == "second version"