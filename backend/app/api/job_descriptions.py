from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.job_description import JobDescriptionCreate, JobDescriptionOut
from app.services.job_description_service import create_job_description, list_job_descriptions

router = APIRouter()


@router.post("", response_model=JobDescriptionOut, status_code=201)
def post_job_description(
    payload: JobDescriptionCreate,
    db: Session = Depends(get_db),
) -> JobDescriptionOut:
    return create_job_description(db, payload)


@router.get("", response_model=list[JobDescriptionOut])
def get_job_descriptions(db: Session = Depends(get_db)) -> list[JobDescriptionOut]:
    return list_job_descriptions(db)
