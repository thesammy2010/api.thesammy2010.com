import dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from src.db import db_lock, session
from src.routers import devices, root
from src.routers.finance import budgets as finance_budgets
from src.routers.finance import migrations as finance_migrations
from src.routers.finance import references as finance_references
from src.routers.finance import transactions as finance_transactions
from src.routers.go_heavier import (
    config,
    exercises,
    health,
    locations,
    migrations,
    sessions,
    workouts,
)
from src.routers.squash import access_requests as squash_access_requests
from src.routers.squash import matches as squash_matches
from src.routers.squash import players as squash_players
from src.routers.squash import reports as squash_reports
from src.routers.squash import venues as squash_venues

dotenv.load_dotenv()


app = FastAPI(
    title="TheSammy2010 API",
    version="1.0.0",
    description=(
        "Backend for TheSammy2010 apps. Currently covers **Go Heavier**, a "
        "personal gym-session tracker: locations, exercises, sessions, and "
        "the individual sets (workouts) logged during them, plus stats "
        "aggregated over each of those, and Apple Health data. It's "
        "`admin`-only for now. Also **Finance**, a record of personal "
        "spending, under `/finance`, which is `admin`-only. And **Squash**, "
        "the matches a group of friends play, under `/squash`, open to the "
        "group's players, whatever their role.\n\n"
        "### Authentication\n"
        "Every endpoint except this documentation requires a Google "
        "Sign-In ID token as a Bearer token. Click **Authorize** below and "
        "paste the token (no need to type `Bearer` yourself).\n\n"
        "### Authorization\n"
        "Endpoints are gated by role - `guest` < `viewer` < `editor` < "
        "`admin`, each including everything the one below it can do, except "
        "managing other users, which is `admin`-only. `/squash` isn't gated "
        "by role: it's open to the group's players, so it reads as `guest`. "
        "The old `squash` role does nothing more than `guest`. New accounts "
        "start as `guest`. `GET /endpoints` maps every route to the role it "
        "requires."
    ),
    openapi_tags=[
        {
            "name": "users",
            "description": "Sign-in and the caller's own account.",
        },
        {
            "name": "devices",
            "description": (
                "The caller's phones, registered for notifications. For "
                "anyone signed in."
            ),
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
            "name": "health",
            "description": (
                "Apple Health data sent by the iOS app: watch workouts, each "
                "linked to the session it was recorded during, and each day's "
                "sleep and body measurements."
            ),
        },
        {
            "name": "migrations",
            "description": (
                "Loads Go Heavier and Finance data from their source Google "
                "Sheets into the database."
            ),
        },
        {
            "name": "transactions",
            "description": "Finance: individual spends. Admin-only.",
        },
        {
            "name": "finance reference data",
            "description": (
                "Finance: the categories, merchants and payment methods a spend "
                "refers to. Admin-only."
            ),
        },
        {
            "name": "budgets",
            "description": (
                "Finance: each category's monthly target, and a month's spending "
                "against them. Admin-only."
            ),
        },
        {
            "name": "squash players",
            "description": (
                "Squash: the people in the group, and their records. Open to "
                "the group's players, whatever their role, and admins; only "
                "admins add players."
            ),
        },
        {
            "name": "squash matches",
            "description": (
                "Squash: singles and doubles matches, from being arranged to "
                "their result, scored game by game."
            ),
        },
        {
            "name": "squash venues",
            "description": (
                "Squash: where the group plays. Only admins add and change them."
            ),
        },
        {
            "name": "squash access requests",
            "description": (
                "Squash: someone signed in who isn't a player asking to join "
                "the group, and admins approving or declining it."
            ),
        },
        {
            "name": "squash ratings and insights",
            "description": (
                "Squash: the Elo ladder, and what matches scored live show "
                "point by point."
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
app.include_router(devices.router)

# The Go Heavier and finance routers are admin-only throughout, set on each
# router. Go Heavier's routes also keep their own minimum role per-route
# (viewer to read, editor to write) for when it's opened up again, since a
# single blanket dependency can't tell GET from POST/PUT/DELETE apart. The
# squash routers are for the group's players, whatever their role, apart from
# asking to join, which is for anyone signed in.
app.include_router(locations.router)
app.include_router(exercises.router)
app.include_router(workouts.router)
app.include_router(config.router)
app.include_router(migrations.router)
app.include_router(sessions.router)
app.include_router(health.router)
app.include_router(finance_transactions.router)
app.include_router(finance_references.router)
app.include_router(finance_budgets.router)
app.include_router(finance_migrations.router)
app.include_router(squash_players.router)
app.include_router(squash_matches.router)
app.include_router(squash_venues.router)
app.include_router(squash_reports.router)
app.include_router(squash_access_requests.router)
