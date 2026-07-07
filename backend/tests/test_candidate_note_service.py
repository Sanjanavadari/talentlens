import pytest
from fastapi import HTTPException

from app.models.candidate import Candidate
from app.schemas.candidate_note import CandidateNoteCreate, CandidateNoteUpdate
from app.services.candidate_note_service import (
    create_note,
    delete_note,
    list_notes_for_candidate,
    update_note,
)


def _create_candidate(db_session, filename: str = "resume.pdf") -> Candidate:
    candidate = Candidate(
        filename=filename,
        raw_text="Sample resume text",
        parsed_fields={"skills": ["python"]},
    )
    db_session.add(candidate)
    db_session.commit()
    db_session.refresh(candidate)
    return candidate


def test_create_note(db_session) -> None:
    candidate = _create_candidate(db_session)
    note = create_note(
        db_session,
        candidate.id,
        CandidateNoteCreate(note_text="Strong backend fit for the platform team."),
    )
    assert note.id is not None
    assert note.candidate_id == candidate.id
    assert note.note_text == "Strong backend fit for the platform team."
    assert note.created_at is not None
    assert note.updated_at is not None


def test_create_note_candidate_not_found(db_session) -> None:
    with pytest.raises(HTTPException) as exc_info:
        create_note(
            db_session,
            999,
            CandidateNoteCreate(note_text="Should not be created."),
        )
    assert exc_info.value.status_code == 404


def test_list_notes_for_candidate(db_session) -> None:
    candidate = _create_candidate(db_session)
    create_note(db_session, candidate.id, CandidateNoteCreate(note_text="First note"))
    create_note(db_session, candidate.id, CandidateNoteCreate(note_text="Second note"))

    notes = list_notes_for_candidate(db_session, candidate.id)
    assert len(notes) == 2
    assert {note.note_text for note in notes} == {"First note", "Second note"}


def test_list_notes_candidate_not_found(db_session) -> None:
    with pytest.raises(HTTPException) as exc_info:
        list_notes_for_candidate(db_session, 999)
    assert exc_info.value.status_code == 404


def test_update_note(db_session) -> None:
    candidate = _create_candidate(db_session)
    created = create_note(
        db_session,
        candidate.id,
        CandidateNoteCreate(note_text="Initial note"),
    )
    updated = update_note(
        db_session,
        created.id,
        CandidateNoteUpdate(note_text="Updated note text"),
    )
    assert updated.id == created.id
    assert updated.note_text == "Updated note text"


def test_update_note_not_found(db_session) -> None:
    with pytest.raises(HTTPException) as exc_info:
        update_note(db_session, 999, CandidateNoteUpdate(note_text="Missing"))
    assert exc_info.value.status_code == 404


def test_delete_note(db_session) -> None:
    candidate = _create_candidate(db_session)
    created = create_note(
        db_session,
        candidate.id,
        CandidateNoteCreate(note_text="To be deleted"),
    )
    delete_note(db_session, created.id)
    notes = list_notes_for_candidate(db_session, candidate.id)
    assert notes == []


def test_delete_note_not_found(db_session) -> None:
    with pytest.raises(HTTPException) as exc_info:
        delete_note(db_session, 999)
    assert exc_info.value.status_code == 404
