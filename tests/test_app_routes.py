"""Tests over the whole app rather than any one endpoint.

These need no database: src.db opens its connection on first use, not on
import, so the app can be built and inspected without one.
"""

import re
from collections import Counter

import pytest
from fastapi.routing import APIRoute

from src.common import ROLE_RANK, UserRole
from src.main import app
from src.resolvers.squash.players import require_squash_player
from src.routers.root import _required_role

ROUTES = [route for route in app.routes if isinstance(route, APIRoute)]
PATH_PARAMETER = re.compile(r"\{[^}]+\}")


def route_ids(route: APIRoute) -> str:
    return f"{sorted(route.methods)[0]} {route.path}"


class TestRouting:
    """Test the routing table as a whole."""

    def test_the_expected_routers_are_mounted(self):
        """A router that is written but never included is silently absent."""
        prefixes = {route.path.split("/")[1] for route in ROUTES}

        assert {"go-heavier", "users", "config", "finance", "squash"} <= prefixes

    @pytest.mark.parametrize(
        "resource",
        [
            "locations",
            "exercises",
            "workouts",
            "sessions",
            "health/workouts",
            "health/days",
        ],
    )
    def test_every_go_heavier_resource_is_reachable(self, resource: str):
        paths = {route.path for route in ROUTES}

        assert f"/go-heavier/{resource}" in paths

    @pytest.mark.parametrize(
        "resource",
        [
            "transactions",
            "categories",
            "merchants",
            "payment-methods",
            "budgets",
            "stats/monthly",
            "stats/yearly",
            "stats/merchants",
            "stats/year-on-year",
            "stats/unusual",
            "stats/breakdown",
            "migrations",
        ],
    )
    def test_every_finance_resource_is_reachable(self, resource: str):
        paths = {route.path for route in ROUTES}

        assert f"/finance/{resource}" in paths

    def test_every_go_heavier_route_is_admin_only(self):
        """Health data especially is private, and the rest is for now."""
        go_heavier = [
            route for route in ROUTES if route.path.startswith("/go-heavier/")
        ]
        not_admin = [
            route_ids(route)
            for route in go_heavier
            if _required_role(route) != UserRole.ADMIN
        ]

        assert go_heavier
        assert not_admin == []

    def test_every_finance_route_is_admin_only(self):
        """Spending is private, so not even a viewer can read it."""
        finance = [route for route in ROUTES if route.path.startswith("/finance/")]
        not_admin = [
            route_ids(route)
            for route in finance
            if _required_role(route) != UserRole.ADMIN
        ]

        assert finance
        assert not_admin == []

    @pytest.mark.parametrize(
        "resource",
        [
            "players",
            "players/me",
            "players/{player_id}/stats",
            "players/{player_id}/head-to-head/{opponent_id}",
            "matches",
            "matches/{match_id}/games/{number}",
            "matches/{match_id}/rallies",
            "matches/{match_id}/rallies/last",
            "matches/{match_id}/complete",
            "matches/{match_id}/merge",
            "matches/{match_id}/insights",
            "venues",
            "venues/{venue_id}",
            "ratings",
            "players/{player_id}/ratings",
            "players/{player_id}/insights",
        ],
    )
    def test_every_squash_resource_is_reachable(self, resource: str):
        paths = {route.path for route in ROUTES}

        assert f"/squash/{resource}" in paths

    def test_every_squash_route_is_for_the_groups_players(self):
        """Being in the group is what lets a friend in, on top of their role."""
        squash = [route for route in ROUTES if route.path.startswith("/squash/")]

        def gates(route: APIRoute) -> set:
            calls = set()

            def collect(dependant) -> None:
                calls.add(dependant.call)
                for sub_dependant in dependant.dependencies:
                    collect(sub_dependant)

            collect(route.dependant)
            return calls

        ungated = [
            route_ids(route)
            for route in squash
            if require_squash_player not in gates(route)
        ]

        assert squash
        assert ungated == []

    def test_squash_needs_no_role(self):
        """Being a player is what lets someone in, so squash routes ask for
        no more than a sign-in, unless they're for admins."""
        gated_by_role = [
            route_ids(route)
            for route in ROUTES
            if route.path.startswith("/squash/")
            and _required_role(route) not in (UserRole.GUEST, UserRole.ADMIN)
        ]

        assert gated_by_role == []

    def test_no_route_asks_for_the_squash_role(self):
        """It's kept only so users given it before still load."""
        asking = [
            route_ids(route)
            for route in ROUTES
            if _required_role(route) == UserRole.SQUASH
        ]

        assert ROLE_RANK[UserRole.SQUASH] < ROLE_RANK[UserRole.VIEWER]
        assert asking == []

    def test_managing_squash_players_and_venues_is_admin_only(self):
        admin = {
            route_ids(route)
            for route in ROUTES
            if route.path.startswith("/squash/")
            and _required_role(route) == UserRole.ADMIN
        }

        assert admin == {
            "POST /squash/players",
            "PUT /squash/players/{player_id}",
            "POST /squash/venues",
            "PUT /squash/venues/{venue_id}",
        }

    def test_no_two_routes_share_a_method_and_path(self):
        """A duplicate is unreachable: the first declared one always wins."""
        seen = Counter(
            (method, route.path) for route in ROUTES for method in route.methods
        )
        duplicates = [pair for pair, count in seen.items() if count > 1]

        assert duplicates == []

    def test_a_fixed_segment_is_declared_before_a_parameter_that_would_match_it(self):
        """/sessions/stats must come before /sessions/{session_id}.

        Routes match in declaration order, so a parameterised route declared
        first swallows every sibling and rejects it as a malformed id.
        """
        offenders = []
        for index, route in enumerate(ROUTES):
            if PATH_PARAMETER.search(route.path) is None:
                continue
            prefix = route.path[: route.path.index("{")]
            for later in ROUTES[index + 1 :]:
                if (
                    later.path.startswith(prefix)
                    and PATH_PARAMETER.search(later.path) is None
                    and later.methods & route.methods
                ):
                    offenders.append(f"{later.path} is shadowed by {route.path}")

        assert offenders == []

    def test_every_route_has_a_response_model_or_returns_no_content(self):
        """Without one the response is not validated or documented."""
        undeclared = [
            route_ids(route)
            for route in ROUTES
            if route.response_model is None and route.status_code != 204
        ]

        assert undeclared == []

    def test_every_route_is_tagged(self):
        """Tags group the endpoints in the generated documentation."""
        untagged = [route_ids(route) for route in ROUTES if not route.tags]

        assert untagged == []


class TestOpenApi:
    """Test the generated schema, which is the published contract."""

    def test_the_schema_generates(self):
        """Every response model has to resolve for this to succeed."""
        assert app.openapi()["info"]["title"] == "TheSammy2010 API"

    def test_every_route_appears_in_the_schema(self):
        paths = app.openapi()["paths"]

        for route in ROUTES:
            assert route.path in paths

    def test_no_operation_ids_collide(self):
        """A collision makes a generated client drop one of the operations."""
        operations = [
            operation["operationId"]
            for path in app.openapi()["paths"].values()
            for operation in path.values()
            if "operationId" in operation
        ]

        assert len(operations) == len(set(operations))

    @pytest.mark.parametrize(
        "path,method",
        [
            ("/go-heavier/sessions", "post"),
            ("/go-heavier/workouts", "post"),
            ("/go-heavier/migrations", "post"),
            ("/finance/transactions", "post"),
            ("/finance/migrations", "post"),
            ("/squash/matches", "post"),
            ("/squash/matches/{match_id}/games/{number}", "put"),
            ("/squash/matches/{match_id}/rallies", "post"),
            ("/squash/venues", "post"),
        ],
    )
    def test_the_write_endpoints_document_a_body(self, path: str, method: str):
        operation = app.openapi()["paths"][path][method]

        assert "requestBody" in operation


class TestCors:
    """Test the origins the browser clients are served from."""

    def test_the_site_and_the_api_are_allowed(self):
        origins = next(
            middleware.kwargs["allow_origins"]
            for middleware in app.user_middleware
            if "allow_origins" in middleware.kwargs
        )

        assert "https://thesammy2010.com" in origins
        assert "https://api.thesammy2010.com" in origins
