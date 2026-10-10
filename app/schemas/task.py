from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.task import TaskStatus


class TaskCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200, examples=["Design the login page"])
    description: str | None = Field(default=None, max_length=5000)

    @field_validator("title")
    @classmethod
    def clean_title(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 3:
            raise ValueError("Title must have at least 3 characters")
        return value

    @field_validator("description")
    @classmethod
    def clean_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None  # empty text is stored as "no description"


class TaskUpdate(TaskCreate):
    """Body of PUT /api/tasks/{id}. It replaces the title and description.
    (Status is NOT here on purpose: it has its own admin-only endpoint.)"""


class TaskStatusUpdate(BaseModel):
    status: TaskStatus


class TaskOwner(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    description: str | None
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    owner: TaskOwner
