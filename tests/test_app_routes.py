"""Tests over the whole app rather than any one endpoint.

These need no database: src.db opens its connection on first use, not on
import, so the app can be built and inspected without one.
"""

import re
from collections import Counter

import pytest
from fastapi.routing import APIRoute

from src.main import app

ROUTES = [route for route in app.routes if isinstance(route, APIRoute)]
PATH_PARAMETER = re.compile(r"\{[^}]+\}")


def route_ids(route: APIRoute) -> str:
    return f"{sorted(route.methods)[0]} {route.path}"


class TestRouting:
    """Test the routing table as a whole."""

    def test_the_expected_routers_are_mounted(self):
        """A router that is written but never included is silently absent."""
        prefixes = {route.path.split("/")[1] for route in ROUTES}

        assert {"go-heavier", "users", "config"} <= prefixes

    @pytest.mark.parametrize(
        "resource", ["locations", "exercises", "workouts", "sessions"]
    )
    def test_every_go_heavier_resource_is_reachable(self, resource: str):
        paths = {route.path for route in ROUTES}

        assert f"/go-heavier/{resource}" in paths

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
