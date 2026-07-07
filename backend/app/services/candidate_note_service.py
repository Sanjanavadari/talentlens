from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.candidate import Candidate
from app.models.candidate_note import CandidateNote
from app.schemas.candidate_note import (
    CandidateNoteCreate,
    CandidateNoteOut,
    CandidateNoteUpdate,
)


def _get_candidate_or_404(db: Session, candidate_id: int) -> Candidate:
    candidate = db.get(Candidate, candidate_id)
    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate {candidate_id} not found.",
        )
    return candidate


def _get_note_or_404(db: Session, note_id: int) -> CandidateNote:
    note = db.get(CandidateNote, note_id)
    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate note {note_id} not found.",
        )
    return note


def create_note(
    db: Session,
    candidate_id: int,
    payload: CandidateNoteCreate,
) -> CandidateNoteOut:
    _get_candidate_or_404(db, candidate_id)
    note = CandidateNote(
        candidate_id=candidate_id,
        note_text=payload.note_text.strip(),
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return CandidateNoteOut.model_validate(note)


def list_notes_for_candidate(
    db: Session,
    candidate_id: int,
) -> list[CandidateNoteOut]:
    _get_candidate_or_404(db, candidate_id)
    notes = (
        db.query(CandidateNote)
        .filter(CandidateNote.candidate_id == candidate_id)
        .order_by(CandidateNote.created_at.desc())
        .all()
    )
    return [CandidateNoteOut.model_validate(note) for note in notes]


def update_note(
    db: Session,
    note_id: int,
    payload: CandidateNoteUpdate,
) -> CandidateNoteOut:
    note = _get_note_or_404(db, note_id)
    note.note_text = payload.note_text.strip()
    db.add(note)
    db.commit()
    db.refresh(note)
    return CandidateNoteOut.model_validate(note)


def delete_note(db: Session, note_id: int) -> None:
    note = _get_note_or_404(db, note_id)
    db.delete(note)
    db.commit()
