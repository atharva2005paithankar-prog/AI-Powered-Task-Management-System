"""Business logic for tasks, including who is allowed to do what.

Rules (from the assignment):
  * Regular user: sees/edits only OWN tasks, cannot change status.
  * Admin: sees/edits ALL tasks and is the only one who can change status.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.exceptions import PermissionDeniedError, TaskNotFoundError
from app.models import Task, TaskStatus, User
from app.schemas.task import TaskCreate, TaskUpdate


def create_task(db: Session, user: User, data: TaskCreate) -> Task:
    # The owner is always the logged-in user, never taken from the request body.
    task = Task(
        user_id=user.id,
        title=data.title,
        description=data.description,
        status=TaskStatus.PENDING.value,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def list_tasks(
    db: Session,
    user: User,
    status: TaskStatus | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[Task]:
    query = select(Task).options(joinedload(Task.owner))  # load owners in the same query
    if not user.is_admin:
        query = query.where(Task.user_id == user.id)
    if status is not None:
        query = query.where(Task.status == status.value)
    query = query.order_by(Task.created_at.desc(), Task.id.desc()).offset(skip).limit(limit)
    return list(db.scalars(query).all())


def get_task_for_user(db: Session, user: User, task_id: int) -> Task:
    """Find a task and make sure this user may access it."""
    task = db.scalar(select(Task).options(joinedload(Task.owner)).where(Task.id == task_id))
    if task is None:
        raise TaskNotFoundError()
    if not user.is_admin and task.user_id != user.id:
        raise PermissionDeniedError("You can only access your own tasks")
    return task


def update_task(db: Session, user: User, task_id: int, data: TaskUpdate) -> Task:
    task = get_task_for_user(db, user, task_id)
    task.title = data.title
    task.description = data.description
    db.commit()
    db.refresh(task)
    return task


def update_task_status(db: Session, task_id: int, new_status: TaskStatus) -> Task:
    # The route already checked the caller is an admin (Depends(require_admin)).
    task = db.scalar(select(Task).options(joinedload(Task.owner)).where(Task.id == task_id))
    if task is None:
        raise TaskNotFoundError()
    task.status = new_status.value
    db.commit()
    db.refresh(task)
    return task
