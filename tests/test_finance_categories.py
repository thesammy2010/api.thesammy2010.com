"""Tests for mapping the finance sheet's categories onto the current ones."""

import decimal
import uuid

import pytest

from src.migration_utils.finance_categories import (
    CATEGORY_GROUPS,
    CATEGORY_NAMESPACE,
    LEGACY_CATEGORIES,
    category_id_for,
    map_category,
)

TEN = decimal.Decimal("10")


class TestCategoryIds:
    def test_the_namespace_is_what_its_comment_says(self):
        assert CATEGORY_NAMESPACE == uuid.uuid5(
            uuid.NAMESPACE_DNS, "finance.thesammy2010.com/categories"
        )

    def test_an_id_is_the_same_on_every_run(self):
        assert category_id_for("Dinner") == category_id_for("Dinner")
        assert category_id_for("Dinner") != category_id_for("Lunch")


class TestMapCategory:
    def test_a_current_category_is_kept(self):
        assert map_category("Groceries", "Tesco", None, TEN) == "Groceries"

    def test_the_sheets_misspelling_is_corrected(self):
        assert map_category("Maintennance", None, None, TEN) == "Maintenance"

    def test_stray_spaces_are_ignored(self):
        assert map_category(" Dinner ", None, None, TEN) == "Dinner"

    def test_no_category_stays_none(self):
        assert map_category(None, "Amazon", "idk", TEN) is None

    def test_an_unknown_category_is_not_guessed(self):
        assert map_category("Something New", None, None, TEN) is None

    @pytest.mark.parametrize("legacy", sorted(LEGACY_CATEGORIES))
    def test_every_older_category_maps_to_a_current_one(self, legacy: str):
        assert map_category(legacy, None, None, TEN) in CATEGORY_GROUPS

    @pytest.mark.parametrize(
        "category,merchant,description,amount,expected",
        [
            ("Eating Out", "Nandos", "Dinner w/ How2Squash", "13.45", "Dinner"),
            ("Eating Out", "Greggs", "Lunch", "4.20", "Lunch"),
            ("Eating Out", "Ole & Steen", "Brunch", "9.00", "Breakfast"),
            ("Eating Out", "Tim Hortons", "Coffee", "3.10", "Coffee"),
            ("Eating Out", "McDonalds", "Two apple pies", "3.38", "Snack"),
            ("Eating Out", "Dishoom", None, "42.00", "Dinner"),
            ("Drinks", "A Random Pub", "w/ Vishal", "14.20", "Drinks - Alcoholic"),
            ("Drinks", "ChaiiWala", None, "3.50", "Drinks - Non-alcoholic"),
            ("Bills", "Shahil Sheth", "Spotify Premium", "4.25", "Media"),
            ("Bills", "LB Harrow", "Council Tax", "175", "Property Related"),
            ("Bills", "Barclays", "Avios Fee", "12", "Utility"),
            ("Bills", "Bristol Bidoof", "Pogo Mapper", "6", "Gaming"),
            ("Bills", "American Express", "Membership fee", "300", "Debt / Credit"),
            ("Travel", "Sutton Carpark", None, "3", "Parking, Tolls & Tickets"),
            ("Travel", "Shell", "Fuel", "60", "Petrol / Fuel"),
            ("Travel", "Uber", None, "12", "Taxis / Private Hire"),
            ("Travel", "TfL", "Oyster top up", "20", "Public Transport"),
            ("Health", "New Image", "Haircut", "18", "Grooming"),
            ("Health", "Boots", "Ibuprofen", "2", "NHS / Medication / Other"),
            ("Activities", "Pokemon GO", "Coins", "1.99", "Gaming"),
            ("Activities", "Vue", "Cinema", "12", "Social & Outings"),
            ("Flights", "RyanAir", "STN", "40", "Holiday"),
        ],
    )
    def test_older_categories_map_from_what_was_bought(
        self, category, merchant, description, amount, expected
    ):
        assert (
            map_category(category, merchant, description, decimal.Decimal(amount))
            == expected
        )
