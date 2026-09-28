from enum import Enum

from .database import get_connection


class Rule(str, Enum):
    DUPLICATE = "duplicate"


def find_duplicates():
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT
                date,
                description,
                amount_in_cents,
                COUNT(*) AS count
            FROM transactions
            GROUP BY date, description, amount_in_cents
            HAVING COUNT(*) > 1
            ORDER BY date DESC;
            """
        ).fetchall()
