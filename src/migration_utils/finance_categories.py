"""The spending categories, and how the sheet's older ones map onto them.

From 2026 the sheet uses the sub categories of its yearly breakdown. Before
that it used a coarser set, such as "Eating Out" or "Bills", which are mapped
here onto the current ones from what the spend was and who it was paid to.

Kept free of any database or config import so that it stays unit testable.
"""

import decimal
import re
import uuid
from typing import Callable, Dict, List, Optional

# uuid5(NAMESPACE_DNS, "finance.thesammy2010.com/categories"), written out so
# that it can never drift with a change to how it was derived.
CATEGORY_NAMESPACE = uuid.UUID("c2495b2a-a9b8-5195-8570-9c8bc4f664f8")

# Main category to its sub categories, in the order of the 2026 breakdown
CATEGORY_TREE: Dict[str, List[str]] = {
    "Food & Drink": [
        "Breakfast",
        "Lunch",
        "Dinner",
        "Snack",
        "Coffee",
        "Drinks - Non-alcoholic",
        "Drinks - Alcoholic",
        "Desserts",
        "Groceries",
    ],
    "Wealth Building": ["Savings", "Investing", "Crypto"],
    "Health & Wellbeing": [
        "Fitness",
        "Grooming",
        "NHS / Medication / Other",
        "Selfcare",
    ],
    "Car & Travel": [
        "Public Transport",
        "Parking, Tolls & Tickets",
        "Maintenance",
        "Cosmetics & Modifications",
        "Petrol / Fuel",
        "Taxis / Private Hire",
    ],
    "Bills & Finance": [
        "Mortgage",
        "Property Related",
        "Debt / Credit",
        "Utility",
        "Donations",
        "Home Improvement",
        "HMRC",
        "Business",
    ],
    "Leisure & Pleasure": [
        "Social & Outings",
        "Gaming",
        "Tech",
        "Gifts",
        "Holiday",
        "Media",
        "Clothes",
        "Other",
    ],
}

CATEGORY_GROUPS: Dict[str, str] = {
    name: group for group, names in CATEGORY_TREE.items() for name in names
}

# How the sheet spells a current category, where that differs from the name
# stored for it
SHEET_SPELLINGS: Dict[str, str] = {"Maintennance": "Maintenance"}


def category_id_for(name: str) -> uuid.UUID:
    """The id of a category, the same on every run."""
    return uuid.uuid5(CATEGORY_NAMESPACE, name)


def _mentions(text: str, *words: str) -> bool:
    return any(re.search(rf"\b{re.escape(word)}", text) for word in words)


def _eating_out(text: str, amount: decimal.Decimal) -> str:
    if _mentions(text, "breakfast", "brunch"):
        return "Breakfast"
    if _mentions(text, "lunch"):
        return "Lunch"
    if _mentions(text, "dinner", "supper"):
        return "Dinner"
    if _mentions(text, "coffee", "latte", "cappuccino", "flat white"):
        return "Coffee"
    if _mentions(text, "dessert", "ice cream", "cake", "waffle", "crepe"):
        return "Desserts"
    if _mentions(text, "drink", "water", "tea", "juice", "coke", "boba"):
        return _drinks(text)
    if _mentions(text, "snack"):
        return "Snack"
    # Nothing says which meal it was, so go by how much it cost
    return "Snack" if amount < 8 else "Dinner"


def _drinks(text: str) -> str:
    if _mentions(
        text,
        "pub",
        "bar",
        "wetherspoon",
        "beer",
        "pint",
        "lager",
        "cider",
        "wine",
        "cocktail",
        "shot",
        "prosecco",
        "asahi",
        "club",
        "opium",
        "ministry of sound",
    ):
        return "Drinks - Alcoholic"
    if _mentions(
        text,
        "water",
        "lucozade",
        "lucazade",
        "chai",
        "tea",
        "juice",
        "coke",
        "boba",
        "matcha",
        "tsujiri",
        "jenki",
        "milkshake",
        "smoothie",
    ):
        return "Drinks - Non-alcoholic"
    return "Drinks - Alcoholic"


def _bills(text: str) -> str:
    if _mentions(text, "pogo", "bidoof"):
        return "Gaming"
    if _mentions(
        text,
        "spotify",
        "youtube",
        "icloud",
        "crunchyroll",
        "netflix",
        "disney",
        "prime",
        "audible",
    ):
        return "Media"
    if _mentions(
        text, "council", "water", "hometree", "lb harrow", "rent", "energy", "edf"
    ):
        return "Property Related"
    if _mentions(text, "american express", "amex"):
        return "Debt / Credit"
    # Phone contracts, insurance and the Avios fee, which the sheet files
    # under Utility from 2025
    return "Utility"


def _travel(text: str) -> str:
    if _mentions(
        text, "parking", "car park", "carpark", "toll", "congestion", "ulez", "dart"
    ):
        return "Parking, Tolls & Tickets"
    if _mentions(
        text,
        "fuel",
        "petrol",
        "diesel",
        "shell",
        "bp",
        "esso",
        "texaco",
        "tesco",
        "asda",
        "sainsbury",
    ):
        return "Petrol / Fuel"
    if _mentions(text, "uber", "taxi", "cab", "bolt", "addison lee"):
        return "Taxis / Private Hire"
    return "Public Transport"


def _health(text: str) -> str:
    if _mentions(text, "haircut", "hair", "barber", "new image", "beard"):
        return "Grooming"
    if _mentions(text, "massage", "spa"):
        return "Selfcare"
    return "NHS / Medication / Other"


def _activities(text: str) -> str:
    if _mentions(
        text,
        "pokemon",
        "pokémon",
        "pogo",
        "niantic",
        "coins",
        "skins",
        "steam",
        "playstation",
        "xbox",
        "nintendo",
    ):
        return "Gaming"
    return "Social & Outings"


# Each of the older categories, given what was bought and from whom along with
# how much it cost, gives the current category it belongs in
LEGACY_CATEGORIES: Dict[str, Callable[[str, decimal.Decimal], str]] = {
    "Eating Out": _eating_out,
    "Drinks": lambda text, amount: _drinks(text),
    "Bills": lambda text, amount: _bills(text),
    "Travel": lambda text, amount: _travel(text),
    "Health": lambda text, amount: _health(text),
    "Activities": lambda text, amount: _activities(text),
    "Home": lambda text, amount: "Home Improvement",
    "Car": lambda text, amount: "Maintenance",
    "Credit": lambda text, amount: "Debt / Credit",
    "Flights": lambda text, amount: "Holiday",
    "L&D": lambda text, amount: "Other",
    "Scouts": lambda text, amount: "Other",
}


def map_category(
    category: Optional[str],
    merchant: Optional[str],
    description: Optional[str],
    amount: decimal.Decimal,
) -> Optional[str]:
    """The current category a sheet row belongs in, or None if it has none.

    A row already in a current category keeps it. One in an older category is
    mapped from its merchant and description, and one in a category this
    doesn't know is left without one rather than guessed at.
    """
    category = (category or "").strip()
    category = SHEET_SPELLINGS.get(category, category)
    if category in CATEGORY_GROUPS:
        return category

    legacy = LEGACY_CATEGORIES.get(category)
    if legacy is None:
        return None

    text = f"{merchant or ''} {description or ''}".lower()
    return legacy(text, amount)
