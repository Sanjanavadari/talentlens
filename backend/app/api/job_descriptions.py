from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.job_description import JobDescriptionCreate, JobDescriptionOut
from app.services.job_description_service import create_job_description, list_job_descriptions

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.post("", response_model=JobDescriptionOut, status_code=201)
def post_job_description(
    payload: JobDescriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobDescriptionOut:
    return create_job_description(db, current_user.id, payload)


@router.get("", response_model=list[JobDescriptionOut])
def get_job_descriptions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[JobDescriptionOut]:
    return list_job_descriptions(db, current_user.id)
