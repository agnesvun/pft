from decimal import ROUND_HALF_UP, Decimal


def to_cents(amount: Decimal) -> int:
    return int((amount * 100).to_integral_value(rounding=ROUND_HALF_UP))


def from_cents(cents: int) -> Decimal:
    return Decimal(cents) / 100
