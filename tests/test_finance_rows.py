"""Tests for reading spends and budgets out of the finance sheet's tabs.

Each tab is given as the rows the Sheets API returns for it: once formatted,
as displayed, and once unformatted.
"""

import datetime
import decimal
import uuid

import pytest

from src.migration_utils.finance_rows import (
    BUDGET_NAMESPACE,
    MERCHANT_NAMESPACE,
    PAYMENT_METHOD_NAMESPACE,
    id_column,
    is_month_tab,
    merchant_id_for,
    parse_amount,
    parse_breakdown_tab,
    parse_currency,
    parse_month_tab,
)
from src.schemas.finance.enums import TimeOfDay

HEADER = [
    "Date",
    "Cost",
    "Cost (GBP)",
    "Card",
    "Who",
    "Category",
    "Neccesary?",
    "Recurring?",
    "When?",
    "w/ Ankita?",
    "Why",
    "Daily",
    "Weekly",
]
SUMMARY = ["30", "", "", "", "", "", "", "", "", "", "", "0", "0"]


def spend(
    date="",
    cost="",
    gbp="£10.00",
    card="Barclaycard",
    who="Tesco",
    category="Groceries",
    necessary="",
    recurring="",
    when="",
    partner="",
    why="",
    row_id=None,
):
    """A formatted row, with the unformatted amounts alongside it."""
    formatted = [
        date,
        cost,
        gbp,
        card,
        who,
        category,
        necessary,
        recurring,
        when,
        partner,
        why,
        "",
        "",
    ]
    if row_id is not None:
        formatted.append(str(row_id))
    return formatted


def raw_of(formatted_rows):
    """The unformatted rows, with amounts as the numbers they display."""
    raw = []
    for row in formatted_rows:
        row = list(row)
        for index in (1, 2):
            if index < len(row) and row[index] and row[index][0] in "£¥€":
                row[index] = float(row[index][1:].replace(",", ""))
        raw.append(row)
    return raw


def parse(*rows, header=HEADER, tab="2026-11"):
    formatted = [header, SUMMARY, *rows]
    return parse_month_tab(tab, formatted, raw_of(formatted))


class TestNamespaces:
    @pytest.mark.parametrize(
        "namespace,table",
        [
            (MERCHANT_NAMESPACE, "merchants"),
            (PAYMENT_METHOD_NAMESPACE, "payment-methods"),
            (BUDGET_NAMESPACE, "budgets"),
        ],
    )
    def test_each_namespace_is_what_its_comment_says(self, namespace, table):
        assert namespace == uuid.uuid5(
            uuid.NAMESPACE_DNS, f"finance.thesammy2010.com/{table}"
        )

    def test_merchants_differing_only_in_case_or_spacing_are_one(self):
        assert merchant_id_for("Pokemon GO") == merchant_id_for(" pokemon  go")


class TestMonthTabs:
    @pytest.mark.parametrize(
        "title,expected",
        [
            ("2026-11", True),
            ("2024-01", True),
            ("2023-12", False),
            ("2026-Breakdown", False),
            ("V1 (deprecated)", False),
        ],
    )
    def test_only_the_current_layouts_months_are_read(self, title, expected):
        assert is_month_tab(title) is expected


class TestParseMonthTab:
    def test_a_days_date_carries_down_to_its_other_spends(self):
        spends = parse(
            spend(date="2026-11-01 Sun", who="Tesco"),
            spend(who="Aldi"),
            spend(date="2026-11-02 Mon", who="Lidl"),
        )

        assert [s.spent_on.day for s in spends] == [1, 1, 2]

    def test_a_spend_above_the_first_date_is_on_the_first_of_the_month(self):
        (first,) = parse(spend(who="Tesco"))

        assert first.spent_on == datetime.date(2026, 11, 1)

    def test_rows_without_an_amount_are_not_spends(self):
        """Including the older tabs' rows holding just the day of the month."""
        spends = parse(
            spend(date="2026-11-01 Sun"),
            ["1", "", "", "", "", "", "", "", "", "", ""],
            ["2026-11-02 Mon"],
        )

        assert len(spends) == 1

    def test_a_day_of_the_month_is_not_taken_as_a_date(self):
        spends = parse(
            spend(date="2026-11-03 Tue"),
            ["4", "", "", "", "", "", "", "", "", "", ""],
            spend(),
        )

        assert spends[-1].spent_on == datetime.date(2026, 11, 3)

    def test_the_amount_is_read_unrounded(self):
        formatted = [HEADER, spend(date="2026-11-01 Sun", gbp="£20.18")]
        raw = raw_of(formatted)
        raw[1][2] = 20.175

        (only,) = parse_month_tab("2026-11", formatted, raw)

        assert only.amount_gbp == decimal.Decimal("20.1750")

    def test_an_amount_is_kept_to_four_places(self):
        formatted = [HEADER, spend(date="2026-11-01 Sun", gbp="£3.33")]
        raw = raw_of(formatted)
        raw[1][2] = 10 / 3

        (only,) = parse_month_tab("2026-11", formatted, raw)

        assert only.amount_gbp == decimal.Decimal("3.3333")

    def test_a_local_amount_keeps_its_currency(self):
        (only,) = parse(spend(date="2026-11-01 Sun", cost="¥1,100", gbp="£5.80"))

        assert only.original_amount == decimal.Decimal("1100")
        assert only.original_currency == "JPY"

    def test_the_yes_no_columns_and_time_of_day_are_read(self):
        (only,) = parse(
            spend(
                date="2026-11-01 Sun",
                necessary="Yes",
                recurring="No",
                partner="Yes",
                when="Evening",
            )
        )

        assert only.is_necessary is True
        assert only.is_recurring is False
        assert only.with_partner is True
        assert only.time_of_day == TimeOfDay.EVENING

    def test_columns_an_older_tab_lacks_are_left_unknown(self):
        header = ["Date", "Cost (GBP)", "Card", "Who", "Category", "Why"]
        formatted = [
            header,
            ["2024-01-01 Mon", "£6.74", "AMEX", "Nandos", "Eating Out", "Dinner"],
        ]
        raw = [
            header,
            ["2024-01-01 Mon", 6.74, "AMEX", "Nandos", "Eating Out", "Dinner"],
        ]

        (only,) = parse_month_tab("2024-01", formatted, raw)

        assert only.is_necessary is None
        assert only.time_of_day is None
        assert only.original_amount is None
        assert only.category == "Dinner"
        assert only.sheet_category == "Eating Out"

    def test_the_card_is_tidied(self):
        (only,) = parse(spend(date="2026-11-01 Sun", card="Cash? "))

        assert only.payment_method == "Cash"

    def test_an_existing_id_is_kept(self):
        row_id = uuid.uuid4()
        (only,) = parse(
            spend(date="2026-11-01 Sun", row_id=row_id), header=HEADER + ["ID"]
        )

        assert only.id == row_id

    def test_a_spend_without_an_id_has_none_yet(self):
        (only,) = parse(spend(date="2026-11-01 Sun"))

        assert only.id is None

    def test_an_invalid_id_names_its_row(self):
        with pytest.raises(ValueError, match="2026-11 row 3"):
            parse(spend(date="2026-11-01 Sun", row_id="nope"), header=HEADER + ["ID"])

    def test_a_spend_remembers_its_row(self):
        spends = parse(spend(date="2026-11-01 Sun"), ["1"], spend())

        assert [s.sheet_row for s in spends] == [3, 5]


class TestIdColumn:
    def test_it_goes_after_the_last_heading(self):
        assert id_column(HEADER + ["", ""]) == len(HEADER)

    def test_an_existing_one_is_found(self):
        assert id_column(HEADER + ["ID"]) == len(HEADER)


class TestParsing:
    @pytest.mark.parametrize(
        "value,expected",
        [
            (12, "12"),
            (20.175, "20.175"),
            ("10.79", "10.79"),
            ("£1,800.00", "1800.00"),
            ("-£5.00", "-5.00"),
            ("", None),
            (None, None),
            ("Est", None),
        ],
    )
    def test_parse_amount(self, value, expected):
        result = parse_amount(value)

        assert result == (None if expected is None else decimal.Decimal(expected))

    @pytest.mark.parametrize(
        "formatted,expected",
        [
            ("¥1,100", "JPY"),
            ("$12.00", "USD"),
            ("US$5", "USD"),
            ("CAD $20", "CAD"),
            ("HK$40", "HKD"),
            ("€31.70", "EUR"),
            ("dh110", "MAD"),
            ("14.00€", "EUR"),
            ("12.00", None),
        ],
    )
    def test_parse_currency(self, formatted, expected):
        assert parse_currency(formatted) == expected


class TestParseBreakdownTab:
    HEADER = ["Main Category", "Sub Category", "Rationale", "Avg", "Target", "January"]

    def test_each_categorys_target_is_read(self):
        budgets = parse_breakdown_tab(
            "2026-Breakdown",
            [
                self.HEADER,
                ["", "", "", "", "based on 2025"],
                ["Food & Drink", "Dinner", "5x/month @ £30", 211.85, 150, 309.74],
                ["Car & Travel", "Maintennance", "", 0, 20.005, 0],
                ["Metrics", "Total", "", 0, 3000, 0],
            ],
        )

        assert [(b.category, b.monthly_target_gbp, b.rationale) for b in budgets] == [
            ("Dinner", decimal.Decimal("150.00"), "5x/month @ £30"),
            ("Maintenance", decimal.Decimal("20.00"), None),
        ]
        assert {b.year for b in budgets} == {2026}

    def test_a_breakdown_without_targets_per_category_has_none(self):
        assert (
            parse_breakdown_tab(
                "2025-Breakdown",
                [
                    ["Main Category", "Sub Category / Month", "Target"],
                    ["", "Lunch", ""],
                ],
            )
            == []
        )
