import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def cli(tmp_path):
    """Run the real entry point with a fresh database outside the repository."""
    source = Path(__file__).resolve().parents[1] / "src"
    env = {**os.environ, "PYTHONPATH": str(source), "NO_COLOR": "1", "COLUMNS": "120"}

    def invoke(*args):
        return subprocess.run(
            [sys.executable, "-c", "from pft.main import main; main()", *args],
            cwd=tmp_path,
            env=env,
            capture_output=True,
            text=True,
            timeout=10,
        )

    return invoke


@pytest.fixture
def transactions(tmp_path):
    def read():
        with sqlite3.connect(tmp_path / "pft.db") as conn:
            conn.row_factory = sqlite3.Row
            return [dict(row) for row in conn.execute("SELECT * FROM transactions ORDER BY id")]

    return read


@pytest.fixture
def add(cli):
    def create(description, amount, category=None, date="2026-09-01"):
        args = ["add", "--desc", description, "--amt", amount, "--date", date]
        if category is not None:
            args.extend(["--category", category])
        result = cli(*args)
        assert result.returncode == 0, result.stdout + result.stderr
        return result

    return create


@pytest.fixture
def csv_file(tmp_path):
    def write(rows, header="date,description,amount,category"):
        path = tmp_path / "transactions.csv"
        path.write_text(header + "\n" + "\n".join(rows) + "\n", encoding="utf-8")
        return str(path)

    return write
