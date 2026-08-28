import dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from src.db import db_lock, session
from src.routers import root
from src.routers.go_heavier import (
    config,
    exercises,
    locations,
    migrations,
    sessions,
    workouts,
)

dotenv.load_dotenv()


app = FastAPI(
    title="TheSammy2010 API",
    version="1.0.0",
    description=(
        "Backend for TheSammy2010 apps. Currently covers **Go Heavier**, a "
        "personal gym-session tracker: locations, exercises, sessions, and "
        "the individual sets (workouts) logged during them, plus stats "
        "aggregated over each of those.\n\n"
        "### Authentication\n"
        "Every endpoint except this documentation requires a Google "
        "Sign-In ID token as a Bearer token. Click **Authorize** below and "
        "paste the token (no need to type `Bearer` yourself).\n\n"
        "### Authorization\n"
        "Endpoints are gated by role - `guest` < `viewer` < `editor` < "
        "`admin`, each including everything the one below it can do, "
        "except managing other users, which is `admin`-only. New accounts "
        "start as `guest`. `GET /endpoints` maps every route to the role "
        "it requires."
    ),
    openapi_tags=[
        {
            "name": "users",
            "description": "Sign-in and the caller's own account.",
        },
        {
            "name": "admin",
            "description": (
                "Provisioning, listing, deleting, and setting the role of other users."
            ),
        },
        {"name": "locations", "description": "Gyms tracked in Go Heavier."},
        {"name": "exercises", "description": "Exercises tracked in Go Heavier."},
        {
            "name": "sessions",
            "description": (
                "One gym visit, grouping the sets logged during it. Deleting a "
                "session deletes its sets."
            ),
        },
        {"name": "workouts", "description": "Individual logged sets."},
        {
            "name": "migrations",
            "description": (
                "Loads Go Heavier data from its source Google Sheet into the database."
            ),
        },
        {
            "name": "default",
            "description": "Static reference data, such as country and muscle group codes.",
        },
    ],
)
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8000",
    "https://api.thesammy2010.com",
    "https://thesammy2010.com",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def guard_shared_db_session(request: Request, call_next):
    """Serializes requests on the shared DB session and self-heals it.

    src.db hands every request the same Session, which SQLAlchemy doesn't
    support touching concurrently - the lock prevents that. Without the
    rollback, a single failed request would leave the session's transaction
    aborted, and every later request sharing it would fail the same way
    until the process restarted.
    """
    async with db_lock:
        try:
            response = await call_next(request)
        except Exception:
            session.rollback()
            raise
        if response.status_code >= 500:
            session.rollback()
        return response


# root.router handles its own auth per-endpoint: POST /users must succeed
# for a caller with a valid Google token who has no User row yet.
app.include_router(root.router)
app.include_router(root.admin_router)

# Every other router declares its own minimum role per-route (viewer to
# read, editor to write), since a single blanket dependency can't tell
# GET from POST/PUT/DELETE apart.
app.include_router(locations.router)
app.include_router(exercises.router)
app.include_router(workouts.router)
app.include_router(config.router)
app.include_router(migrations.router)
app.include_router(sessions.router)
