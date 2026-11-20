# TheSammy2010 API

The backend for TheSammy2010 apps, at https://api.thesammy2010.com, with
interactive docs at [`/docs`](https://api.thesammy2010.com/docs). It covers:

- **Go Heavier** (`/go-heavier`): a gym tracker of locations, exercises,
  sessions and the sets logged in them, with stats, plus Apple Health data from
  the iOS app.
- **Finance** (`/finance`): personal spending, loaded from its Google Sheet,
  with budgets and stats.
- **Squash** (`/squash`): a group of friends' matches, scored live from their
  phones, with venues, records, an Elo ladder and point-by-point insights.

It's FastAPI on Postgres (SQLAlchemy and Alembic), deployed to Fly.io.

## Access

Every endpoint except the docs needs a Google Sign-In ID token as a Bearer
token, from the website's or the iOS app's OAuth client. Signing in for the
first time (`POST /users`) creates a `guest`, and an admin then gives them a
role:

| role | can use |
| --- | --- |
| `guest` | their own account, nothing else |
| `viewer` | reading anything that allows `viewer` |
| `editor` | as `viewer`, and writing |
| `admin` | everything, including managing users |

Go Heavier and Finance are `admin`-only for now. `/squash` doesn't go by role:
it's open to anyone added as a squash player (see [Squash](#squash)), so a
friend who only plays squash stays a `guest`. The old `squash` role does nothing
more than `guest`. `GET /endpoints` maps every route to the role it needs.

```bash
# sign in, or see your account: {"id": "...", "role": "guest"}
curl -X POST localhost:8000/users -H "Authorization: Bearer $TOKEN" | jq

# as an admin: list users, and give one a role
curl localhost:8000/admin/users -H "Authorization: Bearer $TOKEN" | jq
curl -X PATCH localhost:8000/users/$USER_ID/role -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"role": "viewer"}' | jq
```

### Devices

The apps register each phone for notifications with `POST /devices`: its APNs
token, the app's bundle ID, and `sandbox` for a build run from Xcode or
`production` for TestFlight. They send it on every launch, and
`DELETE /devices/{token}` on signing out. A token already registered to someone
else moves to whoever registers it, and deleting an account forgets its phones.
Any signed-in user can register; nothing is sent to them yet.

A role changed straight in the database only takes effect after a restart,
since the app's shared session caches users. Change roles through the API.

## Local development

You need pyenv and Postgres 17 (`brew install postgresql@17`).

```bash
pyenv install 3.13.3

python -m venv .venv
source .venv/bin/activate
pip install poetry==2.1.3
poetry install
pre-commit install

brew services start postgresql@17
createdb api_thesammy2010_com
```

Configuration comes from a `.env`, which isn't tracked. Copy the example, then
fill it in and point `DATABASE_URL` at your local database:

```bash
cp .env.example .env
```

`GOOGLE_SERVICE_ACCOUNT_JSON_BASE64` is a service account key with access to
the spreadsheets, base64 encoded. It's only needed to load data from them. In
production, configuration comes from the Fly app's secrets rather than a file.

`DISABLE_AUTH=true` skips checking Google tokens (never in production), and
every request is then the same `test-user`. Leave it off to sign in as yourself.

### Running the API

```bash
alembic upgrade head
fastapi dev src/main.py   # http://localhost:8000/docs
```

### Tests

```bash
pytest
pre-commit run --all-files   # isort and ruff
```

The tests that touch the database use the one in `.env`. CI runs the
migrations from empty against a throwaway Postgres, then `alembic check` so the
models and migrations can't drift apart unnoticed, then the tests.

### Migrations

Create them with `alembic revision --autogenerate -m "message"`, then check
what it generated: it can't know how to move existing data. Alembic reads
`DATABASE_URL` from the environment, so export the `.env` first
(`set -a; . ./.env; set +a`).

### A copy of production locally

```bash
fly proxy 15432:5432 -a thesammy2010 &
# DATABASE_URL from `fly ssh console -a api-thesammy2010-com -C 'printenv DATABASE_URL'`,
# with the host changed to localhost:15432
pg_dump -Fc --no-owner --no-acl "$PROD_DATABASE_URL" -f prod.dump

dropdb --force api_thesammy2010_com && createdb api_thesammy2010_com
pg_restore --no-owner --no-acl -d api_thesammy2010_com prod.dump
```

It's real personal data (finance and health included), so keep the dump off
anywhere shared, and delete it when you're done.

## Deploying

Merging to `main` deploys: GitHub Actions runs `flyctl deploy`, and Fly runs
`alembic upgrade head` as the release command before switching to the new
version, so a failed migration stops the deploy. The app runs on one machine
that stops when idle and starts on the next request.

```bash
fly status -a api-thesammy2010-com
fly releases -a api-thesammy2010-com
fly postgres connect -a thesammy2010   # a psql shell on production
```

## Go Heavier

### Access

Everything under `/go-heavier`, Apple Health data included, is `admin`-only for
now. Each route still has its own `viewer` (read) or `editor` (write) gate
underneath, so opening it up again is just removing the admin dependency from
each router in `src/routers/go_heavier/`.

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
# create a session, then log sets against it
curl -X POST localhost:8000/go-heavier/sessions \
  -H 'Content-Type: application/json' \
  -d '{"location_id": "'$LOCATION_ID'", "workout_time": "2026-09-01T18:00:00Z"}' | jq

curl "localhost:8000/go-heavier/sessions" | jq

# sessions that included one exercise, though the totals still cover the whole session
curl "localhost:8000/go-heavier/sessions?exercise_id=$EXERCISE_ID" | jq

curl "localhost:8000/go-heavier/sessions/$SESSION_ID" | jq
```

`PATCH /go-heavier/sessions/{session_id}` adds things that aren't known while
a session is being logged: `took_preworkout` and `went_to_office`. Only the
fields given are changed.

```bash
curl -X PATCH "localhost:8000/go-heavier/sessions/$SESSION_ID" \
  -H 'Content-Type: application/json' \
  -d '{"took_preworkout": true}' | jq
```

Deleting a session deletes every set logged against it. The sets belong to the
session and carry neither a location nor a time of their own, so leaving them
would leave rows that cannot be placed.

```bash
curl -X DELETE "localhost:8000/go-heavier/sessions/$SESSION_ID"
```

| query param | default | description |
| --- | --- | --- |
| `location_id` | none | only list sessions at this location |
| `exercise_id` | none | only list sessions that included this exercise |
| `after` / `before` | none | inclusive `workout_time` bounds |
| `page` | `1` | pages of `DEFAULT_DB_PAGE_SIZE` sessions |

Creating a session derives its id from the location and the time in exactly
the way the sheet load does, so the two converge on one row instead of competing
for the unique constraint over that pair. Creating the same one twice is a `409`
carrying the existing id.

The sheet has no session id, so one is derived from the location and the time
with a `uuid5`. That keeps it identical on every run, which is what lets the
sheet load merge onto the existing sessions instead of inserting duplicates.
Correcting a session's time in the sheet therefore produces a new id, leaving
the old session behind to be cleaned up.

### Session stats

`GET /go-heavier/sessions/stats` aggregates across sessions, where
`/sessions/{session_id}` aggregates within one. Averages are taken per session
rather than per set, so they answer what a typical visit looks like.

```bash
curl "localhost:8000/go-heavier/sessions/stats" | jq

curl "localhost:8000/go-heavier/sessions/stats?location_id=$LOCATION_ID&after=2026-01-01T00:00:00Z" | jq
```

| query param | default | description |
| --- | --- | --- |
| `location_id` | none | only count sessions at this location |
| `exercise_id` | none | only count sessions that included this exercise |
| `after` / `before` | none | inclusive `workout_time` bounds |

`average_days_between_sessions` and `longest_gap_days` are null rather than zero
when there are fewer than two sessions to measure between. `by_weekday` is in UK
local time, Monday first, and omits days with no sessions.

Note that the route is declared before `/sessions/{session_id}` in the router, so
that `stats` is not matched as a session id.

### Apple Health

The iOS app reads Apple Health and sends two things, each keyed so it can be
sent any number of times, each recorded against the user who synced it:

- **Workouts** recorded by a watch, `PUT /go-heavier/health/workouts/{id}`,
  where the id is the HealthKit workout's UUID. Duration, calories, average
  /min/max heart rate, METs, the effort rating and every heart rate reading
  (`heart_rate`, `[seconds since start, bpm]` pairs, a JSONB column).
- **Days**, `PUT /go-heavier/health/days/{date}`: the night's sleep by stage
  (dated the day it was woken up on), resting heart rate, HRV, VO2 max, weight
  and body fat, steps.

A workout is linked to the session it was recorded during: the one whose
`workout_time` is between two hours before the workout started and when it
ended, nearest the start, that no other workout already has. Workouts under
five minutes, started by accident, are never matched. Matching runs when a
workout arrives and when a session is created, so either can come first.
`PATCH /go-heavier/health/workouts/{id}` with a `session_id` (or `null`) links
one by hand, and matching leaves it alone after that. Deleting a session
unlinks its workout.

```bash
curl "localhost:8000/go-heavier/health/workouts?session_id=$SESSION_ID" | jq   # no readings
curl "localhost:8000/go-heavier/health/workouts/$WORKOUT_ID" | jq              # with readings
curl "localhost:8000/go-heavier/health/days?after=2026-10-01" | jq
```

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

## Finance

Everything under `/finance` is `admin`-only: spends (`/finance/transactions`),
the categories, merchants and payment methods they refer to, each category's
monthly target (`/finance/budgets`), and stats:

- `/finance/stats/monthly?year=2026&month=11`: a month by category against
  its targets, with a forecast of the month's total while it's in progress
- `/finance/stats/yearly?year=2026`: every category month by month, with
  averages and how far over or under target each is so far
- `/finance/stats/merchants?after=2026-01-01&limit=20`: the merchants most
  spent with and most often spent at
- `/finance/stats/year-on-year?year=2026&month=11`: a month and the year to
  date against the same days a year before, by category
- `/finance/stats/unusual?times_typical=3&min_amount_gbp=20`: spends far above
  their category's median
- `/finance/stats/breakdown?after=2026-01-01&exclude_recurring=true`: spending
  by card, day of the week and time of day

`POST /finance/migrations` loads the finance Google Sheet, one tab per month
from `2024-01`. Each spend row is given a UUID in its tab's `ID` column the
first time it's imported, so importing again updates it rather than adding it
twice. Spends dated after today (the sheet's estimates) aren't imported, and
the pre-2026 categories (`Eating Out`, `Bills`, `Travel`, ...) are mapped onto
the current ones in `src/migration_utils/finance_categories.py`.

```bash
curl -X POST localhost:8000/finance/migrations \
  -H 'Content-Type: application/json' -d '{"dry_run": true}' | jq
```

A spend can belong to another, such as a foreign transaction fee charged
separately from its purchase: set `related_to_id` to the purchase and
`relation` to `fee` (or `refund`, `other`). `GET /finance/transactions/{id}`
then returns the purchase with its fees, `total_gbp` including them, and the
`effective_exchange_rate` that works out to. In the sheet, add a `Related To`
column holding the purchase row's `ID`, and optionally a `Relation` column;
a linked row with no relation is taken to be a fee. Links are one level deep.

Requires `FINANCE_SPREADSHEET_ID`, and the service account needs edit access to
that sheet to write the ids back.

## Squash

Everything under `/squash` is for the squash group's players, whatever their
role, and admins. Being a player is the whole of it: an admin lets a friend in
just by adding them with `POST /squash/players`, giving their Google email, and
takes them out by marking the player inactive. Signing in only makes someone a
`guest`, which opens nothing else, so friends can't read Go Heavier. They're
linked to their user the first time they use `/squash` (or straight away if
they've already signed in). Only admins add and change players. The old
`squash` role is no longer needed and does nothing more than `guest`.

Someone signed in who isn't a player can ask to join instead of asking an admin
some other way. They make, see and withdraw their request at
`/squash/access-requests/me`, with an optional message. Admins list requests at
`GET /squash/access-requests` (`?status=pending` for those waiting), and approve
or decline each. Approving makes them a player: the one given as `player_id`,
such as someone already recorded in matches, else the one they were before or
the one added with their email, else a new player named after their Google
account. Someone declined can withdraw the request and ask again.

When someone deletes their account (or an admin deletes it), their player stays
in every match they played, so everyone else's scores, ratings and unfinished
matches carry on, but it's renamed "Deleted user", loses its email and account
link, and is marked inactive.

Matches are singles or doubles, games to 11 (`points_to`) under point-a-rally
scoring, played on from 10-all until a side is two clear. `best_of` is
optional: without it, whoever won more games wins.

```bash
# arrange a doubles match, sides 1 and 2
curl -X POST localhost:8000/squash/matches -H 'Content-Type: application/json' \
  -d '{"format": "doubles", "best_of": 5, "players": [
        {"player_id": "...", "side": 1}, {"player_id": "...", "side": 1},
        {"player_id": "...", "side": 2}, {"player_id": "...", "side": 2}]}'

# score it live: who won each rally, against the version the phone is showing
curl -X POST localhost:8000/squash/matches/{id}/rallies \
  -H 'Content-Type: application/json' -d '{"won_by_side": 1, "version": 14}'

# a let: replayed, no point, same server. appealed_by_side is optional
curl -X POST localhost:8000/squash/matches/{id}/rallies \
  -H 'Content-Type: application/json' \
  -d '{"decision": "let", "appealed_by_side": 2, "version": 15}'

# a stroke to side 2, or a no let against side 2 (the point to side 1)
curl -X POST localhost:8000/squash/matches/{id}/rallies \
  -H 'Content-Type: application/json' \
  -d '{"won_by_side": 2, "decision": "stroke", "version": 16}'

# take back the last point, such as one given to the wrong side
curl -X DELETE 'localhost:8000/squash/matches/{id}/rallies/last?version=17'

# follow it from another phone: 204 until it moves past version 18
curl 'localhost:8000/squash/matches/{id}?since_version=18'
```

Each response gives the score, `serving_side`, the side to serve next, and
the match's `version`, which goes up on every change. Several people can score
the same match: a rally or undo sent against an older version gets a 409 with
the match as it is now, so two phones scoring the same rally add one point.
The others follow along by polling every second or two with `since_version`. The
point that decides a best-of match completes it, and undoing it reopens it.
`GET /squash/matches/{id}/rallies` is the point-by-point history. A game played
without scoring it live can be entered whole with
`PUT /squash/matches/{id}/games/{number}`. That also corrects a game scored
live, dropping its rallies, since they'd no longer add up to the new score.

A let (`"decision": "let"`) is kept as a rally with no winner, so it's in the
history and can be undone, but adds no point and the same side serves again. A
stroke or a no let is a point like any other, with the call and who appealed
recorded.

A match with `"is_private": true` is only seen in full by admins and its
players. Everyone else still sees it listed with who played and when, but with
`hidden` set and no venue, notes, games or result, gets a 403 for its rallies
and insights, and doesn't have it counted in their stats or head-to-heads.
Private matches never count towards the ratings, since everyone sees those.
Only its players and admins can change one, not whoever arranged it.

Two matches between the same players, such as 2 games recorded and then 1
more, can be merged with `POST /squash/matches/{id}/merge`
(`{"match_id": "<the other>"}`). The one played first is kept with the other's
games after its own, turned round if the players had swapped sides. The merged
match has no `best_of`.

To just play games until you stop, leave out `best_of`. The match then never
ends itself: finish it with `POST /squash/matches/{id}/complete?version=N`.
The side that won more games wins, level is a draw (`winning_side` null), and
a game left unfinished, such as when the court time runs out, doesn't count.

`/squash/players/{id}/stats` is a player's record, draws included, overall and
split into singles and doubles, and
`/squash/players/{id}/head-to-head/{opponent_id}` their matches against one
other player, counting doubles where they were on opposite sides.

Venues are kept in `/squash/venues`, which only admins add to and change, and a
match refers to one by `venue_id` (its response also gives the name). Matches
can be listed by venue with `GET /squash/matches?venue_id=...`.

`GET /squash/ratings` is an Elo ladder over every completed match: everyone
starts on 1000, a win against a higher rated player moves both further, and in
doubles a pair plays as the average of the two, both partners moving together.
`?format=singles` or `doubles` rates each on its own. It's replayed from the
matches on every request, so correcting an old result updates every rating
after it. `/squash/players/{id}/ratings` is one player's history, match by
match.

Matches scored live keep every rally, so `/squash/matches/{id}/insights` and
`/squash/players/{id}/insights` can show:

- points won on serve and on receive;
- the longest run of points;
- game points taken;
- comebacks, meaning games won from 3 or more down, and leads lost;
- deuce games;
- each side's appeals by the call they got: lets, strokes and no lets.

Who served is worked out from who won the rally before, or taken from
`server_id` where it was recorded. Games entered whole only count towards deuce
games.
