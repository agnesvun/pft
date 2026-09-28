import csv
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from .database import get_connection
from .helper import from_cents, to_cents
from .rules import Rule, find_duplicates

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command("add")
def add_transaction(
    description: Annotated[str, typer.Option("--desc", help="Transaction description")],
    amount: Annotated[
        str,
        typer.Option(
            "--amt",
            help="Transaction amount, positive as income, negative as expense, rounded to the nearest cent",
        ),
    ],
    transaction_date: Annotated[
        str | None, typer.Option("--date", help="YYYY-MM-DD, default as today")
    ] = None,
    category: Annotated[
        str | None, typer.Option("--category", help="Optional category")
    ] = None,
):
    if not transaction_date:
        parsed_date = datetime.now().astimezone().date().isoformat()
    else:
        try:
            parsed_date = date.fromisoformat(transaction_date)
        except ValueError:
            console.print(
                f"[red]Invalid date {transaction_date}, expect YYYY-MM-DD[/red]"
            )
            raise typer.Exit(code=1)

    try:
        amt_in_decimal = Decimal(amount)
    except InvalidOperation:
        console.print(f"[red]Invalid amount {amount}[/red]")
        raise typer.Exit(code=1)

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO transactions (
                date,
                description,
                amount_in_cents,
                category
            )
            VALUES (?, ?, ?, ?);
            """,
            (parsed_date, description, to_cents(amt_in_decimal), category),
        )
        console.print(
            f"[green]Added transaction: date={parsed_date} desc={description} amount={amt_in_decimal} category={category} [/green]"
        )


@app.command("import")
def import_csv(
    file: Annotated[
        Path, typer.Option("--file", exists=True, readable=True, help="Path to csv")
    ],
):
    imported = 0
    rejected = 0

    with file.open("r") as f:
        reader = csv.DictReader(f)

        expected_headers = ["date", "description", "amount", "category"]

        if reader.fieldnames != expected_headers:
            console.print("[red]CSV header is not matching[/red]")
            raise typer.Exit(code=1)

        with get_connection() as conn:
            for row_num, row in enumerate(reader, start=2):
                try:
                    tx_date = date.fromisoformat(row["date"])

                    desc = row["description"].strip()
                    if not desc:
                        raise ValueError("Description is empty")

                    category = row["category"].strip() or None

                    amount = Decimal(row["amount"])
                    amount_in_cents = to_cents(amount)

                    conn.execute(
                        """
                        INSERT INTO transactions (
                            date,
                            description,
                            amount_in_cents,
                            category
                        )
                        VALUES (?, ?, ?, ?);
                        """,
                        (tx_date.isoformat(), desc, amount_in_cents, category),
                    )

                    imported += 1
                except (ValueError, InvalidOperation) as exc:
                    rejected += 1
                    console.print(f"[red]Skipped row {row_num}: {exc}[/red]")

    print(f"Imported: {imported}")
    print(f"Rejected: {rejected}")


@app.command("list")
def list_transactions():
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, date, description, amount_in_cents, category
            FROM transactions
            ORDER BY id DESC;
            """
        ).fetchall()

        if not rows:
            print("No transactions found.")
            raise typer.Exit()

        table = Table("ID", "Date", "Description", "Amount", "Category")

        for r in rows:
            table.add_row(
                str(r["id"]),
                r["date"],
                r["description"],
                str(from_cents(r["amount_in_cents"])),
                r["category"],
            )

        console.print(table)


@app.command("categorize")
def categorize_transactions(
    ids: Annotated[
        list[int],
        typer.Option("--id", help="One or more transaction IDs to categorize"),
    ],
    category: Annotated[str, typer.Option("--category", help="Category to set")],
):
    with get_connection() as conn:
        for id in ids:
            cursor = conn.execute(
                "UPDATE transactions SET category = ? WHERE id = ?;", (category, id)
            )
            if cursor.rowcount != 1:
                console.print(
                    f"[red]Transaction ID {id} not found, failed to set category[/red]"
                )
            else:
                console.print(
                    f"[green]Transaction ID {id} category set to {category}[/green]"
                )


@app.command("summarize")
def get_summary():
    with get_connection() as conn:
        totals = conn.execute(
            """
            SELECT
                SUM(CASE WHEN amount_in_cents > 0 THEN amount_in_cents ELSE 0 END) AS income,
                SUM(CASE WHEN amount_in_cents < 0 THEN amount_in_cents ELSE 0 END) AS expense
            FROM transactions;
            """
        ).fetchone()

        categories = conn.execute(
            """
            SELECT
                COALESCE(category, 'Uncategorized') AS category,
                SUM(amount_in_cents) AS total
            FROM transactions
            GROUP BY category
            ORDER BY total ASC;
            """
        ).fetchall()

        total_income = from_cents(totals["income"] or 0)
        total_expense = from_cents(abs(totals["expense"] or 0))
        net = total_income - total_expense

        print(f"Income:  {total_income:.2f}")
        print(f"Expense: {total_expense:.2f}")
        print(f"Net:     {net:.2f}")
        print("---------------------------")
        print("By category (in ASC order):")
        table = Table("Category", "Amount")

        for row in categories:
            amount = from_cents(row["total"])
            table.add_row(row["category"], f"{amount:.2f}")

        console.print(table)


@app.command("analyze")
def analyze(rule: Annotated[Rule, typer.Option("--rule")]):
    match rule:
        case Rule.DUPLICATE:
            rows = find_duplicates()

            table = Table("Date", "Description", "Amount", "Count")

            for r in rows:
                table.add_row(
                    r["date"],
                    r["description"],
                    str(from_cents(r["amount_in_cents"])),
                    str(r["count"]),
                )

            print("Potential duplications:")
            console.print(table)
