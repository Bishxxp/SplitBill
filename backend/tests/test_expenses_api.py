from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier

from app.models import Expense


def expense_payload():
    return {
        "description": "Dinner",
        "paid_by": "alice",
        "amount": "100.00",
        "split": {
            "type": "equal",
            "members": ["alice", "bob", "carol"],
        },
    }


def expense_headers(user="alice", key="dinner-001"):
    return {
        "X-User": user,
        "Idempotency-Key": key,
    }


def test_create_expense(client):
    response = client.post(
        "/groups/1/expenses",
        headers=expense_headers(),
        json=expense_payload(),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["amount"] == "100.00"
    assert data["paid_by"] == "alice"

    assert data["shares"] == {
        "alice": "33.34",
        "bob": "33.33",
        "carol": "33.33",
    }


def test_idempotency(client):
    url = "/groups/1/expenses"

    first = client.post(
        url,
        headers=expense_headers(key="same-key"),
        json=expense_payload(),
    )

    second = client.post(
        url,
        headers=expense_headers(key="same-key"),
        json=expense_payload(),
    )

    assert first.status_code == 201
    assert second.status_code == 201

    assert first.json() == second.json()

    expenses = client.get(
        url,
        headers={"X-User": "alice"},
    )

    assert expenses.status_code == 200
    assert len(expenses.json()) == 1


def test_alice_cannot_write_group_two(client):
    response = client.post(
        "/groups/2/expenses",
        headers=expense_headers(),
        json=expense_payload(),
    )

    assert response.status_code == 403

    assert response.json()["detail"] == ("Not a member of this group")


def test_only_payer_can_delete(client):
    created = client.post(
        "/groups/1/expenses",
        headers=expense_headers(),
        json=expense_payload(),
    )

    assert created.status_code == 201

    expense_id = created.json()["id"]
    url = f"/groups/1/expenses/{expense_id}"

    # Bob tries to delete Alice's expense
    denied = client.delete(
        url,
        headers={"X-User": "bob"},
    )

    assert denied.status_code == 403

    # Alice deletes her own expense
    deleted = client.delete(
        url,
        headers={"X-User": "alice"},
    )

    assert deleted.status_code == 204

    # Deleted expense is no longer listed
    expenses = client.get(
        "/groups/1/expenses",
        headers={"X-User": "alice"},
    )

    assert expenses.json() == []


def test_invalid_exact_split(client):
    payload = {
        "description": "Dinner",
        "paid_by": "alice",
        "amount": "1000.00",
        "split": {
            "type": "exact",
            "shares": {
                "alice": "500.00",
                "bob": "300.00",
                "carol": "100.00",
            },
        },
    }

    response = client.post(
        "/groups/1/expenses",
        headers=expense_headers(),
        json=payload,
    )

    assert response.status_code == 422
    assert response.json()["detail"] == ("The shares do not add up to the total")


def test_reject_three_decimal_places(client):
    payload = expense_payload()
    payload["amount"] = "10.005"

    response = client.post(
        "/groups/1/expenses",
        headers=expense_headers(),
        json=payload,
    )

    assert response.status_code == 422


def test_group_balances_sum_to_zero(client):
    created = client.post(
        "/groups/1/expenses",
        headers=expense_headers(),
        json=expense_payload(),
    )

    assert created.status_code == 201

    response = client.get(
        "/groups/1/balances",
        headers={"X-User": "alice"},
    )

    assert response.status_code == 200

    balances = {
        item["username"]: Decimal(item["balance"])
        for item in response.json()["balances"]
    }

    assert balances == {
        "alice": Decimal("66.66"),
        "bob": Decimal("-33.33"),
        "carol": Decimal("-33.33"),
    }

    assert sum(
        balances.values(),
        Decimal("0.00"),
    ) == Decimal("0.00")


def test_concurrent_idempotency(client):
    url = "/groups/1/expenses"
    barrier = Barrier(4)

    def send_request(_):
        barrier.wait(timeout=15)

        return client.post(
            url,
            headers=expense_headers(key="concurrent-dinner-001"),
            json=expense_payload(),
        )

    # Send 4 requests from different threads
    with ThreadPoolExecutor(max_workers=4) as executor:
        responses = list(executor.map(send_request, range(4)))

    # Every request should succeed
    assert all(response.status_code == 201 for response in responses)

    # Every response should reference the same expense
    expense_ids = [response.json()["id"] for response in responses]

    assert len(set(expense_ids)) == 1

    # Only one expense should exist
    expenses = client.get(
        url,
        headers={"X-User": "alice"},
    )

    assert expenses.status_code == 200
    assert len(expenses.json()) == 1


def test_soft_delete_preserves_record(client, db_session):
    # Create expense
    created = client.post(
        "/groups/1/expenses",
        headers=expense_headers(),
        json=expense_payload(),
    )

    assert created.status_code == 201
    expense_id = created.json()["id"]

    # Delete expense
    deleted = client.delete(
        f"/groups/1/expenses/{expense_id}",
        headers={"X-User": "alice"},
    )

    assert deleted.status_code == 204

    # Check the record directly in PostgreSQL
    db_session.expire_all()
    expense = db_session.get(Expense, expense_id)

    assert expense is not None
    assert expense.is_deleted is True

    # Deleted expense must not affect balances
    response = client.get(
        "/groups/1/balances",
        headers={"X-User": "alice"},
    )

    assert response.status_code == 200

    for member in response.json()["balances"]:
        assert Decimal(member["balance"]) == Decimal("0.00")
