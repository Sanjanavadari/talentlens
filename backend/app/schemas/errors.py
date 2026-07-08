from pydantic import BaseModel


class ErrorResponse(BaseModel):
    detail: str | list[dict[str, object]]
    status_code: int
