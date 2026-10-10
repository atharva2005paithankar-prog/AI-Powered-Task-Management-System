"""Creates the database tables from the models.

Run once:  python -m app.database.init_db
"""
from app import models  # noqa: F401  (importing registers the tables on Base)
from app.database.session import Base, engine


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    print("Database tables are ready: " + ", ".join(Base.metadata.tables))


if __name__ == "__main__":
    init_db()
