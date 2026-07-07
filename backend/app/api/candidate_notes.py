from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.candidate_note import (
    CandidateNoteCreate,
    CandidateNoteOut,
    CandidateNoteUpdate,
)
from app.services.candidate_note_service import (
    create_note,
    delete_note,
    list_notes_for_candidate,
    update_note,
)

candidate_scoped_router = APIRouter()
note_scoped_router = APIRouter()


@candidate_scoped_router.post(
    "/{candidate_id}/notes",
    response_model=CandidateNoteOut,
    status_code=status.HTTP_201_CREATED,
)
def post_candidate_note(
    candidate_id: int,
    payload: CandidateNoteCreate,
    db: Session = Depends(get_db),
) -> CandidateNoteOut:
    return create_note(db, candidate_id, payload)


@candidate_scoped_router.get(
    "/{candidate_id}/notes",
    response_model=list[CandidateNoteOut],
)
def get_candidate_notes(
    candidate_id: int,
    db: Session = Depends(get_db),
) -> list[CandidateNoteOut]:
    return list_notes_for_candidate(db, candidate_id)


@note_scoped_router.patch("/{note_id}", response_model=CandidateNoteOut)
def patch_candidate_note(
    note_id: int,
    payload: CandidateNoteUpdate,
    db: Session = Depends(get_db),
) -> CandidateNoteOut:
    return update_note(db, note_id, payload)


@note_scoped_router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_candidate_note(
    note_id: int,
    db: Session = Depends(get_db),
) -> None:
    delete_note(db, note_id)
