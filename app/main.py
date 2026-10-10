"""App entry point. Start it with:  uvicorn app.main:app --reload"""
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import auth as auth_routes
from app.api import tasks as task_routes
from app.error_handlers import register_error_handlers

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(
    title="AI-Powered Task Management System",
    version="1.0.0",
    description="Task management API with JWT auth, roles (user/admin) and AI-generated task descriptions and summaries.",
)

register_error_handlers(app)
app.include_router(auth_routes.router)
app.include_router(task_routes.router)

# ----- Frontend: plain HTML/CSS/JS served by the same server -----
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/", include_in_schema=False)
def serve_frontend():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
