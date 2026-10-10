from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.ai import service as ai_service
from app.auth.dependencies import get_current_user, require_admin
from app.database.session import get_db
from app.models import TaskStatus, User
from app.schemas.ai import DescriptionResponse, GenerateDescriptionRequest, SummaryResponse
from app.schemas.task import TaskCreate, TaskOut, TaskStatusUpdate, TaskUpdate
from app.services import task_service

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])


# ---------- AI endpoints ----------
# "/generate-description" is declared before "/{task_id}" routes to keep the URLs clear.
@router.post("/generate-description", response_model=DescriptionResponse, tags=["AI"])
def generate_description(
    data: GenerateDescriptionRequest,
    current_user: User = Depends(get_current_user),
):
    """AI Option A: send a task title, get back a description and a checklist."""
    return ai_service.generate_task_description(data.title)


@router.post("/{task_id}/summarize", response_model=SummaryResponse, tags=["AI"])
def summarize_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """AI Option B: summarise one task. You can only summarise tasks you may access."""
    task = task_service.get_task_for_user(db, current_user, task_id)
    return ai_service.summarize_task(task.id, task.title, task.description)


# ---------- Task CRUD ----------
@router.post("", response_model=TaskOut, status_code=201)
def create_task(
    data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a task. It belongs to you and starts as 'Pending'."""
    return task_service.create_task(db, current_user, data)


@router.get("", response_model=list[TaskOut])
def list_tasks(
    status_filter: TaskStatus | None = Query(default=None, alias="status", description="Filter by status"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Users get their own tasks. Admins get everyone's tasks."""
    return task_service.list_tasks(db, current_user, status_filter, skip, limit)


@router.get("/{task_id}", response_model=TaskOut)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return task_service.get_task_for_user(db, current_user, task_id)


@router.put("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Edit title and description. Users: own tasks only. Admins: any task."""
    return task_service.update_task(db, current_user, task_id, data)


@router.patch("/{task_id}/status", response_model=TaskOut)
def update_task_status(
    task_id: int,
    data: TaskStatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Change a task's status. Admin only (regular users get 403)."""
    return task_service.update_task_status(db, task_id, data.status)
