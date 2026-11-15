from decimal import Decimal

import pytest
from app.services.splitting import split_equal, split_exact


def test_equal_split():
    shares = split_equal(
        "100.00",
        ["alice", "bob", "carol"],
    )

    assert shares == {
        "alice": Decimal("33.34"),
        "bob": Decimal("33.33"),
        "carol": Decimal("33.33"),
    }

    assert sum(shares.values()) == Decimal("100.00")


def test_exact_split():
    shares = split_exact(
        "1000.00",
        {
            "alice": "500.00",
            "bob": "300.00",
            "carol": "200.00",
        },
    )

    assert sum(shares.values()) == Decimal("1000.00")


def test_exact_split_invalid_total():
    with pytest.raises(
        ValueError,
        match="The shares do not add up to the total",
    ):
        split_exact(
            "1000.00",
            {
                "alice": "500.00",
                "bob": "300.00",
                "carol": "100.00",
            },
        )


def test_amount_three_decimal_places():
    with pytest.raises(ValueError):
        split_equal(
            "10.005",
            ["alice", "bob"],
        )


def test_duplicate_members():
    with pytest.raises(ValueError):
        split_equal(
            "100.00",
            ["alice", "alice"],
        )


def test_zero_amount():
    with pytest.raises(ValueError):
        split_equal(
            "0.00",
            ["alice", "bob"],
        )