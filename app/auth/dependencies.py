"""FastAPI dependencies that protect endpoints.

    Depends(get_current_user)  -> any logged-in user
    Depends(require_admin)     -> logged-in AND role == admin
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.security import decode_access_token
from app.database.session import get_db
from app.models import User

# auto_error=False lets us return our own 401 message when the header is missing.
bearer_scheme = HTTPBearer(auto_error=False)


def _unauthorized(message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=message,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise _unauthorized("Missing authentication token")

    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        raise _unauthorized("Invalid or expired token")

    # Load the user from the database on every request, so the role is always
    # up to date and a deleted user's old token stops working.
    user = db.get(User, user_id)
    if user is None:
        raise _unauthorized("User no longer exists")
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user
