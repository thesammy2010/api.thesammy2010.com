# TheSammy2010 API

Available at: https://api.thesammy2010.com

### Local development requirements
- pyenv

```bash
pyenv install 3.13.3

python -m venv .venv
source .venv/bin/activate
pip install poetry==2.1.3
poetry install
pre-commit install
```


### Runnning the API
```bash
fastapi dev src/main.py
```

```http request
POST /users
Authorization: Bearer <Google OAuth2 token>
```
```json
{
  "user_id": "<uuid>"
}
```
or
```bash
curl \
  -X POST localhost:8000/users \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Connecting to the database
```bash
fly postgres connect -a thesammy2010
```

or
```bash
fly ssh console -a api-thesammy2010-com
echo $DATABASE_URL
fly proxy 15432:5432 -a thesammy2010
```

### Running migrations
```bash
alembic upgrade head
```

Try to use `alembic revision --autogenerate -m "message"` to create new migrations.

### db for local development
```bash
docker compose up -d postgres
psql -U api -d api_thesammy2010_com
```

### Location stats

`GET /go-heavier/locations/{location_id}/stats` aggregates a location's workout
history. A visit is one distinct `workout_time`, since every set logged in a
session shares that session's timestamp.

```bash
curl "localhost:8000/go-heavier/locations/$LOCATION_ID/stats" | jq

# narrowed to a date range, with a longer exercise breakdown
curl "localhost:8000/go-heavier/locations/$LOCATION_ID/stats?after=2026-05-01T00:00:00Z&before=2026-06-01T00:00:00Z&top_exercises=10" | jq
```

| query param | default | description |
| --- | --- | --- |
| `after` / `before` | none | inclusive `workout_time` bounds |
| `top_exercises` | `5` | size of the per exercise breakdown, 1 to 25 |

`total_volume_kg` and `volume_kg` are the sum of `weight_kg * repetitions`; the
bar and supplementary weights are not included. `average_exercises_per_visit` is
averaged across visits, so it is not `distinct_exercises` divided by `visits`.

### Exercise stats

`GET /go-heavier/exercises/{exercise_id}/stats` is the mirror of the location
stats, aggregated over an exercise instead. A session is one distinct
`workout_time`.

```bash
curl "localhost:8000/go-heavier/exercises/$EXERCISE_ID/stats" | jq

# narrowed to a date range, with a longer location breakdown
curl "localhost:8000/go-heavier/exercises/$EXERCISE_ID/stats?after=2026-05-01T00:00:00Z&before=2026-06-01T00:00:00Z&top_locations=10" | jq
```

| query param | default | description |
| --- | --- | --- |
| `after` / `before` | none | inclusive `workout_time` bounds |
| `top_locations` | `5` | size of the per location breakdown, 1 to 25 |

### Workout stats

`GET /go-heavier/workouts/stats` aggregates across workouts rather than a single
one, since a workout row is one set. Every filter is optional and they combine,
so the same endpoint covers everything, one gym, one exercise, or a date range.
A session is one distinct `workout_time`.

```bash
curl "localhost:8000/go-heavier/workouts/stats" | jq

# one exercise at one gym over a date range
curl "localhost:8000/go-heavier/workouts/stats?location_id=$LOCATION_ID&exercise_id=$EXERCISE_ID&after=2026-05-01T00:00:00Z&before=2026-06-01T00:00:00Z" | jq
```

| query param | default | description |
| --- | --- | --- |
| `location_id` | none | only count workouts at this location |
| `exercise_id` | none | only count workouts of this exercise |
| `after` / `before` | none | inclusive `workout_time` bounds |
| `top_locations` / `top_exercises` | `5` | size of each breakdown, 1 to 25 |

Note that the route is declared before `/workouts/{workout_id}` in the router, so
that `stats` is not matched as a workout id.

### Sessions

A session is one visit to a gym, and owns every set performed while there. It is
a table of its own: `workouts` carries a `session_id`, and the location and the
time live on the session rather than being repeated on all of its sets.

`GET /go-heavier/sessions` lists them most recent first, and
`GET /go-heavier/sessions/{session_id}` returns one with a per exercise
breakdown, ordered by the set each exercise started on.

```bash
curl "localhost:8000/go-heavier/sessions" | jq

# sessions that included one exercise, though the totals still cover the whole session
curl "localhost:8000/go-heavier/sessions?exercise_id=$EXERCISE_ID" | jq

curl "localhost:8000/go-heavier/sessions/$SESSION_ID" | jq
```

| query param | default | description |
| --- | --- | --- |
| `location_id` | none | only list sessions at this location |
| `exercise_id` | none | only list sessions that included this exercise |
| `after` / `before` | none | inclusive `workout_time` bounds |
| `page` | `1` | pages of `DEFAULT_DB_PAGE_SIZE` sessions |

The sheet has no session id, so one is derived from the location and the time
with a `uuid5`. That keeps it identical on every run, which is what lets the
sheet load merge onto the existing sessions instead of inserting duplicates.
Correcting a session's time in the sheet therefore produces a new id, leaving
the old session behind to be cleaned up.

### Loading data from the Google Sheet

`POST /go-heavier/migrations` runs the same load the data migrations run, upserting
rows from the Google Sheet into the database. Tables are always migrated in
dependency order (locations, exercises, sessions, then workouts) regardless of
the order given.

```bash
# everything
curl -X POST localhost:8000/go-heavier/migrations \
  -H 'Content-Type: application/json' -d '{}' | jq

# just the workouts in a date range, without writing anything
curl -X POST localhost:8000/go-heavier/migrations \
  -H 'Content-Type: application/json' \
  -d '{
        "tables": ["workouts"],
        "workouts_after": "2026-06-01T00:00:00Z",
        "workouts_before": "2026-07-01T00:00:00Z",
        "dry_run": true
      }' | jq
```

| field | default | description |
| --- | --- | --- |
| `tables` | all | any of `locations`, `exercises`, `sessions`, `workouts` |
| `dry_run` | `false` | parse the sheet but write nothing |
| `workouts_after` / `workouts_before` | none | inclusive `workout_time` bounds |
| `workouts_row_start` / `workouts_row_end` | whole sheet | sheet row bounds, as used by the data migrations |

Requires `GOOGLE_SERVICE_ACCOUNT_JSON_BASE64` and `GOOGLE_SPREADSHEET_ID`; without
them the endpoint returns `503`.
