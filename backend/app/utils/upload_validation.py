from __future__ import annotations

from fastapi import HTTPException, UploadFile, status

from app.core.config import Settings


def validate_resume_upload(
    upload: UploadFile,
    data: bytes,
    *,
    settings: Settings,
) -> str:
    filename = upload.filename or "resume.pdf"

    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only PDF resumes are supported: {filename}",
        )

    if upload.content_type and upload.content_type not in (
        "application/pdf",
        "application/x-pdf",
        "application/octet-stream",
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid content type for resume upload: {upload.content_type}",
        )

    if len(data) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds upload limit ({settings.max_upload_size_mb} MB): {filename}",
        )

    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Empty file: {filename}",
        )

    if not data.startswith(b"%PDF"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File is not a valid PDF: {filename}",
        )

    return filename


def validate_resume_batch(
    files: list[UploadFile],
    *,
    settings: Settings,
) -> None:
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one resume file is required.",
        )
    if len(files) > settings.max_resumes_per_request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Maximum {settings.max_resumes_per_request} resumes per request "
                f"(received {len(files)})."
            ),
        )
