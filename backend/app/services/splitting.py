import re
from decimal import Decimal


def parse_money(amount: str) -> Decimal:
    if not re.fullmatch(r"\d+(?:\.\d{1,2})?", amount):
        raise ValueError("Amount must have at most 2 decimal places")

    value = Decimal(amount)

    if value <= 0:
        raise ValueError("Amount must be greater than zero")

    if value > Decimal("9999999999.99"):
        raise ValueError("Amount exceeds the supported limit")

    return value


def split_equal(
    amount: str,
    members: list[str],
) -> dict[str, Decimal]:

    if not members:
        raise ValueError("At least one member is required")

    if len(members) != len(set(members)):
        raise ValueError("Duplicate members are not allowed")

    total = parse_money(amount)

    total_satang = int(total * 100)

    base, remainder = divmod(total_satang, len(members))

    shares = {}

    for index, member in enumerate(members):
        extra = 1 if index < remainder else 0

        shares[member] = Decimal(base + extra) / Decimal(100)

    return shares


def parse_share(amount: str) -> Decimal:
    if not re.fullmatch(r"\d+(?:\.\d{1,2})?", amount):
        raise ValueError(
            "Each share must be non-negative and have at most 2 decimal places"
        )

    value = Decimal(amount)

    if value > Decimal("9999999999.99"):
        raise ValueError("Share exceeds the supported limit")

    return value


def split_exact(
    amount: str,
    shares: dict[str, str],
) -> dict[str, Decimal]:

    total = parse_money(amount)

    if not shares:
        raise ValueError("At least one member is required")

    parsed_shares = {member: parse_share(share) for member, share in shares.items()}

    allocated = sum(parsed_shares.values(), Decimal("0.00"))

    if allocated != total:
        raise ValueError("The shares do not add up to the total")

    return parsed_shares
