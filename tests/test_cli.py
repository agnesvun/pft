from datetime import datetime

import pytest


def test_add_persists_between_processes(cli, add, transactions):
    add("Salary", "1000", "income")
    add("Groceries", "-12.345")

    assert transactions() == [
        dict(id=1, date="2026-09-01", description="Salary", amount_in_cents=100000, category="income"),
        dict(id=2, date="2026-09-01", description="Groceries", amount_in_cents=-1235, category=None),
    ]
    result = cli("list")
    assert result.returncode == 0, result.stderr
    assert "Salary" in result.stdout
    assert "Groceries" in result.stdout
    assert "-12.35" in result.stdout


def test_add_defaults_to_local_today(cli, transactions):
    before = datetime.now().astimezone().date().isoformat()
    result = cli("add", "--desc", "Coffee", "--amt", "-3")
    after = datetime.now().astimezone().date().isoformat()
    assert result.returncode == 0, result.stderr
    assert transactions()[0]["date"] in {before, after}


@pytest.mark.parametrize(
    ("option", "value", "message"),
    [("--date", "2026-02-30", "Invalid date"), ("--amt", "not-money", "Invalid amount")],
)
def test_invalid_add_does_not_change_existing_transactions(cli, add, transactions, option, value, message):
    add("Existing", "5")
    before = transactions()
    args = ["add", "--desc", "Invalid", "--amt", "10"]
    if option == "--amt":
        args[-1] = value
    else:
        args.extend([option, value])
    result = cli(*args)
    assert result.returncode != 0
    assert message in result.stdout
    assert "Traceback" not in result.stdout + result.stderr
    assert transactions() == before


def test_empty_database_commands(cli):
    result = cli("list")
    assert result.returncode == 0, result.stderr
    assert "No transactions found" in result.stdout
    result = cli("summarize")
    assert result.returncode == 0, result.stderr
    for label in ("Income", "Expense", "Net"):
        line = next(line for line in result.stdout.splitlines() if line.startswith(label + ":"))
        assert line.split(":")[1].strip() == "0.00"
    result = cli("analyze", "--rule", "duplicate")
    assert result.returncode == 0, result.stderr


def test_import_skips_invalid_rows_and_keeps_valid_rows(cli, csv_file, transactions):
    path = csv_file([
        '2026-09-01,"Salary, monthly",1000,income',
        "2026-02-30,Invalid date,-1,food",
        "2026-09-01,Invalid amount,nope,food",
        "2026-09-01,   ,-1,food",
        "2026-09-02, Coffee ,-3.455,",
    ])
    result = cli("import", "--file", path)
    assert result.returncode == 0, result.stderr
    assert "Imported: 2" in result.stdout
    assert "Rejected: 3" in result.stdout
    assert transactions() == [
        dict(id=1, date="2026-09-01", description="Salary, monthly", amount_in_cents=100000, category="income"),
        dict(id=2, date="2026-09-02", description="Coffee", amount_in_cents=-346, category=None),
    ]


def test_import_rejects_wrong_header_without_changing_data(cli, add, csv_file, transactions):
    add("Existing", "5")
    before = transactions()
    path = csv_file(["2026-09-01,Coffee,-3"], header="date,description,amount")
    result = cli("import", "--file", path)
    assert result.returncode != 0
    assert "CSV header is not matching" in result.stdout
    assert transactions() == before


def test_categorize_multiple_ids_leaves_other_transactions_unchanged(cli, add, transactions):
    add("Apple", "-1", "old")
    add("Bread", "-2")
    add("Rent", "-500", "rent")
    before = transactions()
    result = cli("categorize", "--id", "1", "--id", "2", "--category", "groceries")
    assert result.returncode == 0, result.stderr
    expected = [{**row, "category": "groceries"} if row["id"] in {1, 2} else row for row in before]
    assert transactions() == expected


def test_summary_totals_categories_and_uncategorized(cli, add):
    add("Salary", "1000", "income")
    add("Apple", "-12.34", "food")
    add("Bread", "-7.66", "food")
    add("Bus", "-5")
    result = cli("summarize")
    assert result.returncode == 0, result.stderr
    totals = dict(line.split(":", 1) for line in result.stdout.splitlines() if line.startswith(("Income:", "Expense:", "Net:")))
    assert {key: value.strip() for key, value in totals.items()} == {
        "Income": "1000.00", "Expense": "25.00", "Net": "975.00",
    }
    for category, amount in [("food", "-20.00"), ("Uncategorized", "-5.00")]:
        line = next(line for line in result.stdout.splitlines() if category in line)
        assert amount in line


def test_duplicate_analysis_matches_date_description_and_amount(cli, add):
    add("Duplicate", "-10", "food")
    add("Duplicate", "-10", "other")
    add("Duplicate", "-10", date="2026-09-02")
    add("Duplicate", "-11")
    add("Unique", "-10")
    result = cli("analyze", "--rule", "duplicate")
    assert result.returncode == 0, result.stderr
    rows = [line for line in result.stdout.splitlines() if "Duplicate" in line]
    assert len(rows) == 1
    assert [cell.strip() for cell in rows[0].split("│")[1:-1]] == [
        "2026-09-01", "Duplicate", "-10", "2",
    ]
    assert "Unique" not in result.stdout
