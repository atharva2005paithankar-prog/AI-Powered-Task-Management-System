"""Business logic for users (no HTTP code here)."""
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.security import hash_password, verify_password
from app.exceptions import EmailAlreadyExistsError
from app.models import User, UserRole
from app.schemas.user import UserCreate


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower()))


def create_user(db: Session, data: UserCreate, role: UserRole = UserRole.USER) -> User:
    if get_user_by_email(db, data.email):
        raise EmailAlreadyExistsError()

    user = User(
        name=data.name,
        email=data.email.lower(),
        password=hash_password(data.password),
        role=role.value,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        # Two people registered the same email at the same moment.
        db.rollback()
        raise EmailAlreadyExistsError()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """Return the user if the email and password are right, otherwise None."""
    user = get_user_by_email(db, email)
    if user is None or not verify_password(password, user.password):
        return None
    return user
