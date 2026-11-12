"""Turning the finance sheet's monthly tabs into spends.

Each month has its own tab, named like "2026-11", with one row per spend. A
day's date is only filled in on its first spend, and the older tabs also have
a row per day holding just the day of the month, which isn't a spend. A row is
a spend when it has an amount in GBP, and each one is given an id in the tab's
ID column, so that it keeps the same id however often it is imported.

Kept free of any database or config import so that it stays unit testable.
"""

import dataclasses
import datetime
import decimal
import logging
import re
import uuid
from typing import Any, Dict, List, Optional, Sequence, Tuple

from src.migration_utils.finance_categories import (
    CATEGORY_GROUPS,
    SHEET_SPELLINGS,
    map_category,
)
from src.schemas.finance.enums import PaymentMethodKind, TimeOfDay

logger = logging.getLogger(__name__)

# uuid5(NAMESPACE_DNS, "finance.thesammy2010.com/<table>"), written out so
# that they can never drift with a change to how they were derived.
MERCHANT_NAMESPACE = uuid.UUID("9891e1e0-4222-5afe-b078-3870b203c5c8")
PAYMENT_METHOD_NAMESPACE = uuid.UUID("af8e401d-4b96-5a89-a51d-540b74513aa6")
BUDGET_NAMESPACE = uuid.UUID("2ed7083b-77b2-5df6-be8d-d70525f9cd85")

MONTH_TAB = re.compile(r"^(\d{4})-(\d{2})$")
BREAKDOWN_TAB = re.compile(r"^(\d{4})-Breakdown$")
# The first month in the current layout. 2023-12 predates the Cost (GBP)
# column and is not imported.
FIRST_MONTH = "2024-01"

ID_HEADER = "ID"

# A formatted date such as "2026-11-01 Sun". The rows that hold only the day
# of the month don't match, which is what keeps them from being taken as dates.
SHEET_DATE = re.compile(r"^(\d{4}-\d{2}-\d{2})\b")

PAYMENT_METHODS: Dict[str, PaymentMethodKind] = {
    "Barclaycard": PaymentMethodKind.CREDIT_CARD,
    "AMEX": PaymentMethodKind.CREDIT_CARD,
    "Barclays": PaymentMethodKind.DEBIT_CARD,
    "Monzo": PaymentMethodKind.DEBIT_CARD,
    "Revolut": PaymentMethodKind.DEBIT_CARD,
    "Cash": PaymentMethodKind.CASH,
    "Splitwise": PaymentMethodKind.SHARED_EXPENSE,
    "Suica": PaymentMethodKind.TRANSIT_CARD,
}
# How the sheet writes a payment method, where that differs from its name
PAYMENT_METHOD_SPELLINGS: Dict[str, str] = {"Cash?": "Cash"}

# The symbol or code on a local currency amount, longest first so that "CAD $"
# is matched before "$". It's usually in front, but some amounts have it after,
# such as "14.00€". A bare "$" was always spent in the US.
CURRENCY_MARKERS: Sequence[Tuple[str, str]] = (
    ("CAD $", "CAD"),
    ("CA$", "CAD"),
    ("CAD", "CAD"),
    ("US$", "USD"),
    ("HK$", "HKD"),
    ("HKD", "HKD"),
    ("TT$", "TTD"),
    ("$", "USD"),
    ("¥", "JPY"),
    ("€", "EUR"),
    ("£", "GBP"),
    ("dh", "MAD"),
    ("₦", "NGN"),
    ("₺", "TRY"),
)

# The places a spend's amounts and a budget's target are stored to. A spend
# split three ways on Splitwise has more than that in the sheet.
SPEND_PLACES = decimal.Decimal("0.0001")
BUDGET_PLACES = decimal.Decimal("0.01")

TIMES_OF_DAY: Dict[str, TimeOfDay] = {kind.value: kind for kind in TimeOfDay}


@dataclasses.dataclass
class SheetSpend:
    """One spend read from a month's tab, before it's turned into a model."""

    tab: str
    sheet_row: int
    id: Optional[uuid.UUID]
    spent_on: datetime.date
    amount_gbp: decimal.Decimal
    original_amount: Optional[decimal.Decimal]
    original_currency: Optional[str]
    payment_method: str
    merchant: Optional[str]
    # The current category the sheet's one maps to, and the sheet's own
    category: Optional[str]
    sheet_category: Optional[str]
    description: Optional[str]
    is_necessary: Optional[bool]
    is_recurring: Optional[bool]
    with_partner: Optional[bool]
    time_of_day: Optional[TimeOfDay]


@dataclasses.dataclass
class SheetBudget:
    year: int
    category: str
    monthly_target_gbp: decimal.Decimal
    rationale: Optional[str]


def is_month_tab(title: str) -> bool:
    return MONTH_TAB.match(title) is not None and title >= FIRST_MONTH


def merchant_key(name: str) -> str:
    """Two spellings of a merchant differing only in case or spacing are one."""
    return " ".join(name.split()).casefold()


def merchant_id_for(name: str) -> uuid.UUID:
    return uuid.uuid5(MERCHANT_NAMESPACE, merchant_key(name))


def payment_method_id_for(name: str) -> uuid.UUID:
    return uuid.uuid5(PAYMENT_METHOD_NAMESPACE, name)


def budget_id_for(category: str, year: int) -> uuid.UUID:
    return uuid.uuid5(BUDGET_NAMESPACE, f"{category}|{year}")


def clean_payment_method(name: str) -> str:
    name = " ".join(name.split())
    return PAYMENT_METHOD_SPELLINGS.get(name, name)


def payment_method_kind(name: str) -> PaymentMethodKind:
    return PAYMENT_METHODS.get(name, PaymentMethodKind.OTHER)


def _text(value: Any) -> Optional[str]:
    """A cell's text, or None when it's blank."""
    if value is None:
        return None
    value = " ".join(str(value).split())
    return value or None


def parse_amount(value: Any) -> Optional[decimal.Decimal]:
    """An unformatted cell as an amount, or None when it doesn't hold one.

    Numbers come back from the sheet as numbers, but a cell that was typed as
    text, such as "10.79" or "£10.79", comes back as that text.
    """
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        # Through str so a float like 20.175 isn't stored as its binary
        # approximation
        return decimal.Decimal(str(value))

    text = re.sub(r"[£,\s]", "", str(value))
    if not re.fullmatch(r"-?\d+(\.\d+)?", text):
        return None
    return decimal.Decimal(text)


def parse_currency(formatted: Optional[str]) -> Optional[str]:
    """The ISO 4217 code of a formatted local currency amount, such as "¥1,100"."""
    text = _text(formatted)
    if text is None:
        return None
    for marker, code in CURRENCY_MARKERS:
        if text.startswith(marker) or text.endswith(marker):
            return code
    return None


def parse_yes_no(value: Any) -> Optional[bool]:
    text = (_text(value) or "").lower()
    if text == "yes":
        return True
    if text == "no":
        return False
    return None


def parse_time_of_day(value: Any) -> Optional[TimeOfDay]:
    return TIMES_OF_DAY.get((_text(value) or "").lower())


def parse_sheet_date(value: Any) -> Optional[datetime.date]:
    match = SHEET_DATE.match(_text(value) or "")
    if not match:
        return None
    return datetime.date.fromisoformat(match.group(1))


def id_column(header: Sequence[Any]) -> int:
    """The index of the tab's ID column, or of where it should be added.

    It goes after the last heading rather than at the start, so that adding it
    doesn't move any of the columns the tab's formulas refer to.
    """
    names = [_text(cell) for cell in header]
    if ID_HEADER in names:
        return names.index(ID_HEADER)
    filled = [index for index, name in enumerate(names) if name]
    return filled[-1] + 1 if filled else 0


def _cell(row: Sequence[Any], index: Optional[int]) -> Any:
    if index is None or index >= len(row):
        return None
    return row[index]


def parse_month_tab(
    tab: str, formatted: List[List[Any]], raw: List[List[Any]]
) -> List[SheetSpend]:
    """Every spend in a month's tab.

    ``formatted`` is the tab as it's displayed, which is what gives the dates
    and the currency of a local amount. ``raw`` is the same tab unformatted,
    which gives the amounts without rounding them to the penny.
    """
    if not formatted:
        return []

    header = [_text(cell) for cell in formatted[0]]
    columns = {name: index for index, name in enumerate(header) if name}
    ids = id_column(formatted[0])

    def column(name: str) -> Optional[int]:
        return columns.get(name)

    year, month = (int(part) for part in MONTH_TAB.match(tab).groups())
    # A spend above the tab's first date is taken to be on the first of the month
    spent_on = datetime.date(year, month, 1)

    spends: List[SheetSpend] = []
    for offset, row in enumerate(formatted[1:], start=1):
        raw_row = raw[offset] if offset < len(raw) else []
        sheet_row = offset + 1

        date = parse_sheet_date(_cell(row, column("Date")))
        if date is not None:
            spent_on = date

        amount_gbp = parse_amount(_cell(raw_row, column("Cost (GBP)")))
        if amount_gbp is None:
            continue
        amount_gbp = amount_gbp.quantize(SPEND_PLACES)

        payment_method = _text(_cell(row, column("Card")))
        if payment_method is None:
            logger.warning(f"Skipping {tab} row {sheet_row}, it has no card")
            continue

        row_id = _text(_cell(row, ids))
        try:
            spend_id = uuid.UUID(row_id) if row_id else None
        except ValueError:
            raise ValueError(f"{tab} row {sheet_row} has an invalid ID: {row_id}")

        merchant = _text(_cell(row, column("Who")))
        description = _text(_cell(row, column("Why")))
        sheet_category = _text(_cell(row, column("Category")))
        category = map_category(sheet_category, merchant, description, amount_gbp)
        if sheet_category and category is None:
            logger.warning(
                f"{tab} row {sheet_row} has an unknown category, {sheet_category}"
            )

        original_amount = parse_amount(_cell(raw_row, column("Cost")))
        if original_amount is not None:
            original_amount = original_amount.quantize(SPEND_PLACES)
        spends.append(
            SheetSpend(
                tab=tab,
                sheet_row=sheet_row,
                id=spend_id,
                spent_on=spent_on,
                amount_gbp=amount_gbp,
                original_amount=original_amount,
                original_currency=(
                    parse_currency(_cell(row, column("Cost")))
                    if original_amount is not None
                    else None
                ),
                payment_method=clean_payment_method(payment_method),
                merchant=merchant,
                category=category,
                sheet_category=sheet_category,
                description=description,
                is_necessary=parse_yes_no(_cell(row, column("Neccesary?"))),
                is_recurring=parse_yes_no(_cell(row, column("Recurring?"))),
                with_partner=parse_yes_no(_cell(row, column("w/ Ankita?"))),
                time_of_day=parse_time_of_day(_cell(row, column("When?"))),
            )
        )

    return spends


def parse_breakdown_tab(tab: str, raw: List[List[Any]]) -> List[SheetBudget]:
    """The monthly target of each category in a year's breakdown.

    Only a breakdown with a Target and a Sub Category column has targets per
    category, which so far is 2026's. The Metrics rows are totals, not
    categories, so they never match one and are skipped.
    """
    match = BREAKDOWN_TAB.match(tab)
    if not match or not raw:
        return []

    header = [_text(cell) for cell in raw[0]]
    if "Target" not in header or "Sub Category" not in header:
        return []
    target = header.index("Target")
    sub_category = header.index("Sub Category")
    rationale = header.index("Rationale") if "Rationale" in header else None

    budgets: List[SheetBudget] = []
    for row in raw[1:]:
        category = _text(_cell(row, sub_category))
        category = SHEET_SPELLINGS.get(category, category)
        amount = parse_amount(_cell(row, target))
        if category not in CATEGORY_GROUPS or amount is None:
            continue
        budgets.append(
            SheetBudget(
                year=int(match.group(1)),
                category=category,
                monthly_target_gbp=amount.quantize(BUDGET_PLACES),
                rationale=_text(_cell(row, rationale)),
            )
        )
    return budgets
