# AI-Powered Task Management System

A task manager built with **Python + FastAPI + PostgreSQL**. Users sign in with **JWT**, manage their own tasks, and
an **AI service** drafts task descriptions and summarises tasks. Admins can see and manage every task.
A small web frontend (plain HTML/CSS/JS) is served by the same app, so one command runs everything.

## Project overview

| Area | What it does |
|---|---|
| Authentication | Register, login, JWT access token, passwords stored as bcrypt hashes |
| Authorization | Two roles: `user` and `admin` (rules below) |
| Tasks | Create, list, view, update, update status. Every task belongs to the user who created it |
| AI (both options built) | **Option A:** generate a task description. **Option B:** summarise a task |
| Frontend | Sign in / register screen and a status board (Pending, In Progress, Testing, Completed) |
| Quality | Layered structure, validation, clear HTTP status codes, 50 automated tests, Postman collection |

### Access control

| Action | Regular user | Admin |
|---|---|---|
| Register / login | yes | yes |
| Create a task | yes (owned by them) | yes (owned by them) |
| List / view tasks | **own** tasks only | **all** tasks |
| Edit title / description | **own** tasks only | any task |
| Update task status | **no** (403) | yes |
| Use the AI features | yes (on tasks they can access) | yes |

## Python version

Python 3.11 or newer (developed on 3.12).

## Setup instructions

1. Create and activate a virtual environment

python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

2. Install dependencies

pip install -r requirements.txt

3. Start PostgreSQL (option A: Docker, option B: your own install, see "Database configuration")

docker compose up -d

4. Create your .env file and edit it (secret key + AI settings)

cp .env.example .env              # Windows: copy .env.example .env

5. Create the tables, then add test users and sample tasks

python -m app.database.init_db
python -m app.database.seed

6. Run the app

uvicorn app.main:app --reload

Then open:

* Web app: http://localhost:8000
* Interactive API docs (Swagger): http://localhost:8000/docs
* Health check: http://localhost:8000/health

## Database configuration

The database is chosen by one setting, `DATABASE_URL`, in `.env`.

* PostgreSQL with Docker: `docker compose up -d` creates a database called `task_manager` on port 5432. The credentials in
  `docker-compose.yml` and `.env.example` are local development defaults only.
* PostgreSQL installed locally: create an empty database (`createdb task_manager`) and put your user and password in `DATABASE_URL`.
* MySQL: run `pip install pymysql cryptography`, create an empty database, and set
  `DATABASE_URL=mysql+pymysql://USER:PASSWORD@localhost:3306/task_manager`.

Schema and seeders (no SQL file): the tables are defined as Python models in `app/models/`.
`python -m app.database.init_db` creates them and `python -m app.database.seed` adds sample data.
Both commands are safe to run again.

Tables:

* `users`: id, name, email (unique), password (bcrypt hash), role (`user`/`admin`), created_at, updated_at
* `tasks`: id, user_id (foreign key to users), title, description, status, created_at, updated_at

## Environment variables

| Variable | Meaning | Example |
|---|---|---|
| `DATABASE_URL` | Database connection string | `postgresql+psycopg2://postgres:postgres@localhost:5432/task_manager` |
| `SECRET_KEY` | Secret used to sign JWT tokens | output of `python -c "import secrets; print(secrets.token_hex(32))"` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | How long a login token stays valid | `60` |
| `AI_PROVIDER` | `gemini`, `openai`, `anthropic` or `mock` | `gemini` |
| `AI_API_KEY` | Your API key for that provider | (your own key) |
| `AI_MODEL` | Optional model name, empty = provider default | `gemini-3.8-flash` |
| `AI_TIMEOUT_SECONDS` | How long to wait for the AI provider | `30` |


## AI configuration

1. Get an API key from your provider (Google AI Studio for Gemini, platform.openai.com for OpenAI, console.anthropic.com for Anthropic).
2. In `.env`, set `AI_PROVIDER` and `AI_API_KEY`.
3. Restart the server.

| `AI_PROVIDER` | Default model (override with `AI_MODEL`) |
|---|---|
| `gemini` | `gemini-2.5-flash` |
| `openai` | `gpt-4o-mini` |
| `anthropic` | `claude-haiku-5-5` |
| `mock` | no key needed. A fake AI for tests and offline demos. Its answers are labelled `[mock AI]` |

Model names change over time. If the API answers with an error such as HTTP 404, check the provider's documentation
for a current model name and put it in `AI_MODEL`. The full provider error is written to the server log.

**If the key is missing or wrong**, the AI endpoints return a clear error (503 or 502) and the rest of the app keeps working.

## How to run

uvicorn app.main:app --reload     # start the app (web UI + API)
pytest                            # run all automated tests (no API key and no PostgreSQL needed)

The tests use a temporary in-memory SQLite database and the mock AI provider, so they never touch your real data.

## API endpoints

All task and AI endpoints need the header `Authorization: Bearer <token>`.

| Method | URL | Who | Description |
|---|---|---|---|
| POST | `/api/auth/register` | public | Create an account (role is always `user`) |
| POST | `/api/auth/login` | public | Returns a JWT access token |
| GET | `/api/auth/me` | logged in | The current user |
| POST | `/api/tasks` | logged in | Create a task (starts as `Pending`) |
| GET | `/api/tasks` | logged in | List tasks (own, or all for admin). Query: `status`, `skip`, `limit` |
| GET | `/api/tasks/{id}` | owner or admin | View one task |
| PUT | `/api/tasks/{id}` | owner or admin | Update title and description |
| PATCH | `/api/tasks/{id}/status` | **admin only** | Update status: `Pending`, `In Progress`, `Testing`, `Completed` |
| POST | `/api/tasks/generate-description` | logged in | **AI Option A:** body `{"title": "..."}` returns a description and checklist |
| POST | `/api/tasks/{id}/summarize` | owner or admin | **AI Option B:** returns a short summary and key points |

Example login:

curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "User@123"}'

### HTTP status codes used

| Code | When |
|---|---|
| 200 / 201 | Success / created |
| 401 | Missing or invalid/expired JWT, wrong email or password |
| 403 | Logged in but not allowed (another user's task, or a user changing status) |
| 404 | Task not found |
| 409 | Email already registered |
| 422 | Invalid request data (short title, bad email, unknown status...) |
| 500 / 503 | Database error / database unavailable |
| 502 | AI provider failed or returned an unusable answer |
| 503 | AI not configured (no key or unknown provider) |
| 504 | AI provider timed out |

## Test credentials

Created by `python -m app.database.seed` (for local testing only):

| Role | Email | Password |
|---|---|---|
| admin | `admin@example.com` | `Admin@123` |
| user | `user@example.com` | `User@123` |
| user | `bob@example.com` | `Bob@1234` |

## AI feature implemented

Both options from the assignment are implemented, in the `app/ai/` package:

* **Option A, Generate Task Description:** `POST /api/tasks/generate-description`. The title goes in, and a description plus a short checklist comes back.
  In the web app, click **Draft description with AI** in the New task dialog.
* **Option B, Generate Task Summary:** `POST /api/tasks/{id}/summarize`. The task's title and description go in, and a concise summary plus key points come back.
  In the web app, click **Summarize with AI** on a task card.

How it works:

1. `prompts.py` builds a prompt that demands **JSON in an exact shape**. User text is escaped and wrapped in tags, and the model is told to treat it as data (protection against prompt injection).
2. `providers.py` sends the prompt to the chosen provider over HTTPS (Gemini, OpenAI or Anthropic). Timeouts, network errors and HTTP errors become clean errors.
3. `parsing.py` pulls the JSON out of the reply (models sometimes add code fences or extra text).
4. `service.py` **validates** the JSON with Pydantic (`app/schemas/ai.py`). If the answer is badly formatted it retries once, then returns 502.
5. The API key lives only in the environment and is never logged or returned. Raw provider errors go to the log, not to the client.

## Project structure

app/
├─ main.py            # creates the app, registers routes, serves the frontend
├─ config.py          # settings from environment variables
├─ exceptions.py      # our own error types
├─ error_handlers.py  # turns errors into JSON responses
├─ api/               # routes (URLs): auth.py, tasks.py
├─ auth/              # security.py (bcrypt + JWT), dependencies.py (login/admin checks)
├─ models/            # database tables: user.py, task.py
├─ schemas/           # request/response shapes and validation: user.py, task.py, ai.py
├─ services/          # business logic and permission rules: user_service.py, task_service.py
├─ ai/                # prompts, providers, JSON parsing, AI service, AI errors, mock
└─ database/          # session.py, init_db.py (schema), seed.py (sample data)
frontend/              # index.html, style.css, app.js
tests/                 # pytest tests
postman/               # Postman collection
docs/                  # interview preparation notes

Request flow: `route (api/) -> dependency checks the JWT (auth/) -> service applies the rules (services/) -> model talks to the database (models/) -> schema shapes the response`.

## Postman

Import `postman/AI_Task_Manager.postman_collection.json`. Run the seeder first, then run the five folders **in order**
with the Collection Runner. The login requests save the tokens and task ids in collection variables. It covers:
registration, login, regular user task APIs, admin task APIs, authorization failures (403/401/404/422) and the AI endpoints.
If your server is not on port 8000, change the `baseUrl` collection variable.

## Important assumptions and decisions

* **Self-registration always creates a `user`.** Admins are created by the seeder only, so nobody can make themselves admin.
* **Status changes are admin-only**, exactly as the assignment says. `PUT /api/tasks/{id}` therefore edits only title and description. New tasks start as `Pending`.
* **403 for another user's task** (not 404). It states clearly that access is denied. Some teams use 404 to hide that the task exists.
* **Admins see all tasks** and tasks stay owned by their creator. An admin who creates a task owns it.
* **The role is read from the database on every request**, not trusted from the token, so a role change or deleted user takes effect immediately.
* **Same error for wrong email and wrong password**, so attackers cannot find out which emails are registered.
* **Schema via SQLAlchemy models + `init_db`** (allowed by the assignment: "migrations/schema"). Alembic migrations would be the next step for a team project.
* **Normal (sync) endpoints**, not async. FastAPI runs them in a thread pool, which keeps the code simple to read and explain.
* **The mock AI provider** exists for automated tests and offline demos only. Real AI is used whenever `AI_PROVIDER` is `gemini`, `openai` or `anthropic` with a key.
* **The frontend stores the JWT in `localStorage`.** That is simple for a demo. A production app would prefer an HttpOnly cookie. The UI never uses `innerHTML`, which reduces the XSS risk.
* AI results are shown to the user and are **not** saved automatically: the user decides whether to keep the draft.

## Not included on purpose

`.env`, API keys, real passwords, `venv/` and a separate `.sql` file are not part of the project, as required.
