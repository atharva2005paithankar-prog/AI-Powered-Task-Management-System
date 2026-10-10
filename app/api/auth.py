from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.security import create_access_token
from app.database.session import get_db
from app.exceptions import InvalidCredentialsError
from app.models import User
from app.schemas.user import TokenOut, UserCreate, UserLogin, UserOut
from app.services import user_service

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(data: UserCreate, db: Session = Depends(get_db)):
    """Create a new account. New accounts always get the 'user' role."""
    return user_service.create_user(db, data)


@router.post("/login", response_model=TokenOut)
def login(data: UserLogin, db: Session = Depends(get_db)):
    """Check email + password and return a JWT access token."""
    user = user_service.authenticate_user(db, data.email, data.password)
    if user is None:
        # Same message for "wrong email" and "wrong password" on purpose.
        raise InvalidCredentialsError()
    return TokenOut(access_token=create_access_token(user.id), user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)):
    """Return the logged-in user (used by the frontend to restore a session)."""
    return current_user
