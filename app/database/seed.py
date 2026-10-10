"""Seeder: adds test users and sample tasks.

Run after init_db:  python -m app.database.seed
It is safe to run more than once (it skips data that already exists).
"""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.init_db import init_db
from app.database.session import SessionLocal
from app.models import Task, TaskStatus, UserRole
from app.schemas.user import UserCreate
from app.services import user_service

# These are TEST credentials for local use only (they are listed in the README).
SEED_USERS = [
    {"name": "Admin User", "email": "admin@example.com", "password": "Admin@123", "role": UserRole.ADMIN},
    {"name": "Alice Sharma", "email": "user@example.com", "password": "User@123", "role": UserRole.USER},
    {"name": "Bob Mehta", "email": "bob@example.com", "password": "Bob@1234", "role": UserRole.USER},
]

SEED_TASKS = {
    "admin@example.com": [
        ("Review pull requests", "Check open pull requests and leave feedback for the team.", TaskStatus.IN_PROGRESS),
    ],
    "user@example.com": [
        ("Design the login page", "Create a simple login screen with email and password fields.", TaskStatus.PENDING),
        ("Write API documentation", "Document every endpoint with an example request and response.", TaskStatus.IN_PROGRESS),
        ("Fix signup validation bug", "The signup form accepts very short passwords. Add a minimum length check.", TaskStatus.TESTING),
    ],
    "bob@example.com": [
        ("Set up the database", "Install PostgreSQL and create the task_manager database.", TaskStatus.COMPLETED),
        ("Plan the next sprint", None, TaskStatus.PENDING),
    ],
}


def seed_database(db: Session) -> None:
    for item in SEED_USERS:
        user = user_service.get_user_by_email(db, item["email"])
        if user is None:
            user = user_service.create_user(
                db,
                UserCreate(name=item["name"], email=item["email"], password=item["password"]),
                role=item["role"],
            )
            print(f"Created {item['role'].value}: {item['email']}")

        # Add sample tasks only if this user has none yet.
        task_count = db.scalar(select(func.count(Task.id)).where(Task.user_id == user.id))
        if task_count == 0:
            for title, description, status in SEED_TASKS.get(item["email"], []):
                db.add(Task(user_id=user.id, title=title, description=description, status=status.value))
            db.commit()


if __name__ == "__main__":
    init_db()  # make sure the tables exist
    with SessionLocal() as session:
        seed_database(session)
    print("Seeding finished.")
