from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    # This column is called "password" (as the assignment asks) but it only
    # ever stores a bcrypt HASH, never the real password.
    password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(10), default=UserRole.USER.value, server_default=UserRole.USER.value)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    tasks: Mapped[list["Task"]] = relationship(back_populates="owner", cascade="all, delete-orphan")

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN.value
