import pytest
from pydantic import ValidationError

from src.schemas.go_heavier.exercises import ExerciseRequest
from src.schemas.go_heavier.locations import LocationRequest

VALID_URLS = [
    "https://example.com/logo.png",
    "http://example.com",
    "https://assets.jhtbrand.co/files/product/0f950e18101ad94229c87b3c3d2e03a33f/",
    "https://example.com/image.jpg?v=1&size=large",
]
BLANK_VALUES = [None, "", "   "]
INVALID_URLS = ["not a url", "example.com/logo.png", "/relative/path.png", "https://"]


def _exercise(image_url) -> ExerciseRequest:
    return ExerciseRequest(name="Bench Press", image_url=image_url)


def _location(logo_url) -> LocationRequest:
    return LocationRequest(
        name="The Gym Wealdstone", address_country_iso3="GBR", logo_url=logo_url
    )


class TestExerciseImageUrl:
    """Test URL validation on an exercise's image."""

    @pytest.mark.parametrize("url", VALID_URLS)
    def test_valid_urls_are_kept(self, url: str):
        assert _exercise(url).image_url == url

    @pytest.mark.parametrize("value", BLANK_VALUES)
    def test_blank_values_become_none(self, value):
        """Existing rows hold an empty string where no image was set."""
        assert _exercise(value).image_url is None

    @pytest.mark.parametrize("url", INVALID_URLS)
    def test_invalid_urls_are_rejected(self, url: str):
        with pytest.raises(ValidationError):
            _exercise(url)

    def test_surrounding_whitespace_is_stripped(self):
        assert _exercise("  https://example.com  ").image_url == "https://example.com"


class TestLocationLogoUrl:
    """Test URL validation on a location's logo, which mirrors the exercise image."""

    @pytest.mark.parametrize("url", VALID_URLS)
    def test_valid_urls_are_kept(self, url: str):
        assert _location(url).logo_url == url

    @pytest.mark.parametrize("value", BLANK_VALUES)
    def test_blank_values_become_none(self, value):
        assert _location(value).logo_url is None

    @pytest.mark.parametrize("url", INVALID_URLS)
    def test_invalid_urls_are_rejected(self, url: str):
        with pytest.raises(ValidationError):
            _location(url)

    def test_logo_url_defaults_to_none(self):
        assert (
            LocationRequest(
                name="The Gym Wealdstone", address_country_iso3="GBR"
            ).logo_url
            is None
        )
