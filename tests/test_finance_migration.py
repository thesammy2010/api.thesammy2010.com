"""Tests for importing the finance sheet.

The spreadsheet is replaced with a fake that records what's written to it,
and every run is a dry run or is rejected before writing, so these need no
credentials or database.
"""

import datetime
import uuid
from types import SimpleNamespace

import pendulum
import pytest

from src.migration_utils import finance_sheet
from src.migration_utils.finance_sheet import FinanceWorkbook
from src.resolvers.finance import migrations
from src.resolvers.finance.migrations import FinanceMigrationValidationError
from src.resolvers.go_heavier.migrations import MigrationConfigurationError
from src.schemas.finance.migrations import FinanceTable, RunFinanceMigrationRequest

HEADER = ["Date", "Cost (GBP)", "Card", "Who", "Category", "Why"]
EXISTING = uuid.UUID("5f0c3c39-2b4e-4b8e-9a64-2f7f5b2d7f10")


class FakeSpreadsheet:
    def __init__(self):
        self.updates = []
        self.added_columns = {}

    def values_batch_update(self, body):
        self.updates.extend(body["data"])

    def worksheet(self, title):
        spreadsheet = self

        class Worksheet:
            def add_cols(self, cols):
                spreadsheet.added_columns[title] = cols

        return Worksheet()


def workbook(*rows, header=HEADER, tab="2026-11", column_count=26):
    formatted = [header, *rows]
    raw = [
        [float(cell[1:]) if str(cell).startswith("£") else cell for cell in row]
        for row in formatted
    ]
    return FinanceWorkbook(
        spreadsheet=FakeSpreadsheet(),
        months={tab: (formatted, raw)},
        breakdowns={},
        merchants=["Tesco"],
        column_counts={tab: column_count},
    )


@pytest.fixture
def sheet(monkeypatch):
    """Install a fake finance sheet, returning a setter for its workbook."""
    monkeypatch.setattr(
        migrations,
        "cfg",
        SimpleNamespace(
            google_service_account_filepath="sa.json", FINANCE_SPREADSHEET_ID="sheet"
        ),
    )
    # Fixed so the spends' dates are never in the future
    monkeypatch.setattr(
        migrations.pendulum,
        "today",
        lambda tz: pendulum.datetime(2026, 11, 12, tz=tz),
    )

    def set_workbook(book: FinanceWorkbook) -> FinanceWorkbook:
        monkeypatch.setattr(finance_sheet, "read_workbook", lambda cfg: book)
        return book

    return set_workbook


def run(**kwargs):
    return migrations.run_migration(RunFinanceMigrationRequest(dry_run=True, **kwargs))


def result_for(response, table: FinanceTable):
    return next(result for result in response.results if result.table == table)


class TestFinanceMigration:
    def test_a_dry_run_reads_every_table_without_writing(self, sheet):
        book = sheet(
            workbook(
                ["2026-11-01 Sun", "£12.50", "Barclaycard", "Tesco", "Groceries", ""],
                ["", "£3.00", "Cash", "Greggs", "Eating Out", "Snack"],
            )
        )

        response = run()

        assert response.ids_assigned == 2
        assert book.spreadsheet.updates == []
        assert result_for(response, FinanceTable.TRANSACTIONS).rows == 2
        assert result_for(response, FinanceTable.PAYMENT_METHODS).rows == 2
        assert result_for(response, FinanceTable.MERCHANTS).rows == 2
        assert all(result.written == 0 for result in response.results)

    def test_tables_are_migrated_after_the_ones_they_reference(self, sheet):
        sheet(workbook(["2026-11-01 Sun", "£1.00", "Cash", "", "", ""]))

        tables = [result.table for result in run().results]

        assert tables.index(FinanceTable.TRANSACTIONS) > max(
            tables.index(FinanceTable.CATEGORIES),
            tables.index(FinanceTable.MERCHANTS),
            tables.index(FinanceTable.PAYMENT_METHODS),
        )
        assert tables.index(FinanceTable.BUDGETS) > tables.index(
            FinanceTable.CATEGORIES
        )

    def test_spends_dated_after_today_are_not_imported(self, sheet):
        sheet(
            workbook(
                ["2026-11-12 Thu", "£1.00", "Cash", "", "", ""],
                ["2026-11-13 Fri", "£1800.00", "Barclays", "", "Mortgage", "Est"],
            )
        )

        response = run()

        assert result_for(response, FinanceTable.TRANSACTIONS).rows == 1
        # It's still given an id, so it keeps it once it's imported
        assert response.ids_assigned == 2

    def test_spends_can_be_narrowed_by_date(self, sheet):
        sheet(
            workbook(
                ["2026-11-01 Sun", "£1.00", "Cash", "", "", ""],
                ["2026-11-05 Thu", "£2.00", "Cash", "", "", ""],
            )
        )

        response = run(after=datetime.date(2026, 11, 2))

        assert result_for(response, FinanceTable.TRANSACTIONS).rows == 1

    def test_uncategorised_spends_are_counted(self, sheet):
        sheet(workbook(["2026-11-01 Sun", "£1.00", "Cash", "", "", ""]))

        assert run().uncategorised == 1

    def test_a_row_the_api_would_reject_rejects_the_import(self, sheet):
        sheet(workbook(["2026-11-01 Sun", "£1.00", "Cash", "", "", "x" * 600]))

        with pytest.raises(FinanceMigrationValidationError) as error:
            run()

        assert error.value.table == FinanceTable.TRANSACTIONS

    def test_it_needs_the_spreadsheet_configured(self, sheet, monkeypatch):
        monkeypatch.setattr(
            migrations,
            "cfg",
            SimpleNamespace(
                google_service_account_filepath="sa.json", FINANCE_SPREADSHEET_ID=None
            ),
        )

        with pytest.raises(MigrationConfigurationError):
            run()


class TestAssignMissingIds:
    def spends(self, book):
        return finance_sheet.read_spends(book)

    def test_new_ids_go_in_an_added_id_column(self):
        book = workbook(
            ["2026-11-01 Sun", "£1.00", "Cash", "", "", ""],
            ["1", "", "", "", "", ""],
            ["", "£2.00", "Cash", "", "", ""],
        )
        spends = self.spends(book)

        assigned = finance_sheet.assign_missing_ids(book, spends, write=True)

        assert assigned == 2
        updates = {u["range"]: u["values"][0][0] for u in book.spreadsheet.updates}
        assert updates.pop("'2026-11'!G1") == "ID"
        assert updates == {
            "'2026-11'!G2": str(spends[0].id),
            "'2026-11'!G4": str(spends[1].id),
        }

    def test_an_existing_id_is_left_alone(self):
        book = workbook(
            ["2026-11-01 Sun", "£1.00", "Cash", "", "", "", str(EXISTING)],
            ["", "£2.00", "Cash", "", "", "", ""],
            header=HEADER + ["ID"],
        )
        spends = self.spends(book)

        finance_sheet.assign_missing_ids(book, spends, write=True)

        assert spends[0].id == EXISTING
        assert book.spreadsheet.updates == [
            {"range": "'2026-11'!G3", "values": [[str(spends[1].id)]]}
        ]

    def test_nothing_is_written_when_every_spend_has_an_id(self):
        book = workbook(
            ["2026-11-01 Sun", "£1.00", "Cash", "", "", "", str(EXISTING)],
            header=HEADER + ["ID"],
        )

        finance_sheet.assign_missing_ids(book, self.spends(book), write=True)

        assert book.spreadsheet.updates == []

    def test_a_tab_too_narrow_for_the_column_is_widened(self):
        book = workbook(["2026-11-01 Sun", "£1.00", "Cash", "", "", ""], column_count=6)

        finance_sheet.assign_missing_ids(book, self.spends(book), write=True)

        assert book.spreadsheet.added_columns == {"2026-11": 1}
