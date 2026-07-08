from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.job_description import JobDescription
from app.schemas.job_description import JobDescriptionCreate, JobDescriptionOut


def list_job_descriptions(db: Session, recruiter_id: int) -> list[JobDescriptionOut]:
    job_descriptions = (
        db.query(JobDescription)
        .filter(JobDescription.recruiter_id == recruiter_id)
        .order_by(JobDescription.created_at.desc())
        .all()
    )
    return [JobDescriptionOut.model_validate(jd) for jd in job_descriptions]


def create_job_description(
    db: Session,
    recruiter_id: int,
    payload: JobDescriptionCreate,
) -> JobDescriptionOut:
    job_description = JobDescription(
        recruiter_id=recruiter_id,
        title=payload.title.strip(),
        text=payload.text.strip(),
    )
    db.add(job_description)
    db.commit()
    db.refresh(job_description)
    return JobDescriptionOut.model_validate(job_description)


def get_job_description_or_404(
    db: Session,
    job_description_id: int,
    recruiter_id: int,
) -> JobDescription:
    job_description = (
        db.query(JobDescription)
        .filter(
            JobDescription.id == job_description_id,
            JobDescription.recruiter_id == recruiter_id,
        )
        .first()
    )
    if job_description is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job description {job_description_id} not found.",
        )
    return job_description
