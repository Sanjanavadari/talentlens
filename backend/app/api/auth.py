from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import TokenResponse, UserLogin, UserOut, UserRegister
from app.services.auth_service import login_user, register_user

router = APIRouter()


@router.post("/register", response_model=UserOut, status_code=201)
def post_register(
    payload: UserRegister,
    db: Session = Depends(get_db),
) -> UserOut:
    return register_user(db, payload)


@router.post("/login", response_model=TokenResponse)
def post_login(
    payload: UserLogin,
    db: Session = Depends(get_db),
) -> TokenResponse:
    return login_user(db, payload)


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(current_user)
