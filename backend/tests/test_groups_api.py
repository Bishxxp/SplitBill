def test_alice_can_list_own_groups(client):
    response = client.get(
        "/groups",
        headers={"X-User": "alice"},
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["name"] == "Chiang Mai trip"


def test_bob_can_list_two_groups(client):
    response = client.get(
        "/groups",
        headers={"X-User": "bob"},
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2


def test_alice_cannot_access_group_two(client):
    response = client.get(
        "/groups/2",
        headers={"X-User": "alice"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == ("Not a member of this group")


def test_unknown_group_returns_404(client):
    response = client.get(
        "/groups/999",
        headers={"X-User": "alice"},
    )

    assert response.status_code == 404
