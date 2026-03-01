"""Tests for game creation and retrieval endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_game(client: AsyncClient):
    """POST /api/games creates a game in LOBBY status with a 6-char code."""
    response = await client.post("/api/games")

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert "code" in data
    assert len(data["code"]) == 6
    assert data["code"] == data["code"].upper()  # uppercase
    assert data["code"].isalnum()
    assert data["status"] == "lobby"


@pytest.mark.asyncio
async def test_get_game_by_code(client: AsyncClient):
    """GET /api/games/{code} returns full game details."""
    # Create a game first.
    create_resp = await client.post("/api/games")
    code = create_resp.json()["code"]

    response = await client.get(f"/api/games/{code}")

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == code
    assert data["status"] == "lobby"
    assert data["host_id"] is None
    assert data["players"] == []
    assert data["rooms"] == []
    assert data["weapons"] == []


@pytest.mark.asyncio
async def test_get_game_case_insensitive(client: AsyncClient):
    """GET /api/games/{code} works with lowercase code."""
    create_resp = await client.post("/api/games")
    code = create_resp.json()["code"]

    response = await client.get(f"/api/games/{code.lower()}")
    assert response.status_code == 200
    assert response.json()["code"] == code


@pytest.mark.asyncio
async def test_get_game_not_found(client: AsyncClient):
    """GET /api/games/{code} returns 404 for non-existent code."""
    response = await client.get("/api/games/ZZZZZZ")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_game_shows_players_after_join(client: AsyncClient):
    """GET /api/games/{code} includes players who have joined."""
    create_resp = await client.post("/api/games")
    code = create_resp.json()["code"]

    await client.post(f"/api/games/{code}/players", json={"name": "Alice"})
    await client.post(f"/api/games/{code}/players", json={"name": "Bob"})

    response = await client.get(f"/api/games/{code}")
    data = response.json()

    assert len(data["players"]) == 2
    names = {p["name"] for p in data["players"]}
    assert names == {"Alice", "Bob"}

    # Players should not expose token in game detail.
    for player in data["players"]:
        assert "token" not in player
