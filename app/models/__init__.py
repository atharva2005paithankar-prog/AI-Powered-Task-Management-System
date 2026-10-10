# Import every model here so SQLAlchemy knows about all tables.
from app.models.task import Task, TaskStatus
from app.models.user import User, UserRole

__all__ = ["Task", "TaskStatus", "User", "UserRole"]
