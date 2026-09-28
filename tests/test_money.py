from decimal import Decimal

import pytest

from pft.helper import from_cents, to_cents


@pytest.mark.parametrize(
    ("amount", "cents"),
    [
        ("0", 0),
        ("0.29", 29),
        ("12.344", 1234),
        ("12.345", 1235),
        ("-12.344", -1234),
        ("-12.345", -1235),
        ("0.005", 1),
        ("-0.005", -1),
    ],
)
def test_rounds_to_cents_half_up(amount, cents):
    assert to_cents(Decimal(amount)) == cents


@pytest.mark.parametrize("cents", [0, 1, -1, 29, 12345, -12345])
def test_cents_convert_back_to_exact_decimal(cents):
    amount = from_cents(cents)
    assert isinstance(amount, Decimal)
    assert amount == Decimal(cents).scaleb(-2)
    assert to_cents(amount) == cents
