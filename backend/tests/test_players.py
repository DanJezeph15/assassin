"""Tests for player join endpoint and auth dependency."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_join_game(client: AsyncClient):
    """POST /api/games/{code}/players creates a player and returns a token."""
    create_resp = await client.post("/api/games")
    code = create_resp.json()["code"]

    response = await client.post(
        f"/api/games/{code}/players",
        json={"name": "Alice"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Alice"
    assert "id" in data
    assert "token" in data
    assert len(data["token"]) == 64  # 32 bytes hex = 64 chars


@pytest.mark.asyncio
async def test_first_player_becomes_host(client: AsyncClient):
    """The first player to join a game becomes the host."""
    create_resp = await client.post("/api/games")
    code = create_resp.json()["code"]

    join_resp = await client.post(
        f"/api/games/{code}/players",
        json={"name": "Alice"},
    )
    player_id = join_resp.json()["id"]

    game_resp = await client.get(f"/api/games/{code}")
    assert game_resp.json()["host_id"] == player_id


@pytest.mark.asyncio
async def test_second_player_does_not_become_host(client: AsyncClient):
    """Only the first player becomes host; subsequent players do not."""
    create_resp = await client.post("/api/games")
    code = create_resp.json()["code"]

    first_resp = await client.post(
        f"/api/games/{code}/players",
        json={"name": "Alice"},
    )
    first_id = first_resp.json()["id"]

    await client.post(
        f"/api/games/{code}/players",
        json={"name": "Bob"},
    )

    game_resp = await client.get(f"/api/games/{code}")
    assert game_resp.json()["host_id"] == first_id  # Still Alice


@pytest.mark.asyncio
async def test_duplicate_name_rejected(client: AsyncClient):
    """Joining with a name already taken in the game returns 400."""
    create_resp = await client.post("/api/games")
    code = create_resp.json()["code"]

    await client.post(f"/api/games/{code}/players", json={"name": "Alice"})

    response = await client.post(
        f"/api/games/{code}/players",
        json={"name": "Alice"},
    )

    assert response.status_code == 400
    assert "already taken" in response.json()["detail"]


@pytest.mark.asyncio
async def test_duplicate_name_case_insensitive(client: AsyncClient):
    """Name uniqueness check is case-insensitive."""
    create_resp = await client.post("/api/games")
    code = create_resp.json()["code"]

    await client.post(f"/api/games/{code}/players", json={"name": "Alice"})

    response = await client.post(
        f"/api/games/{code}/players",
        json={"name": "alice"},
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_join_nonexistent_game(client: AsyncClient):
    """Joining a non-existent game returns 404."""
    response = await client.post(
        "/api/games/ZZZZZZ/players",
        json={"name": "Alice"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_join_game_not_in_lobby(client: AsyncClient, db: AsyncSession):
    """Cannot join a game that is not in LOBBY status."""
    from app.models.game import Game, GameStatus
    from app.utils.codes import generate_game_code

    code = await generate_game_code(db)
    game = Game(code=code, status=GameStatus.IN_PROGRESS)
    db.add(game)
    await db.commit()

    response = await client.post(
        f"/api/games/{code}/players",
        json={"name": "Alice"},
    )

    assert response.status_code == 400
    assert "not in the lobby" in response.json()["detail"]


@pytest.mark.asyncio
async def test_join_name_validation_empty(client: AsyncClient):
    """Joining with an empty name returns 422 (validation error)."""
    create_resp = await client.post("/api/games")
    code = create_resp.json()["code"]

    response = await client.post(
        f"/api/games/{code}/players",
        json={"name": ""},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_join_name_validation_whitespace_only(client: AsyncClient):
    """Joining with a whitespace-only name returns 422."""
    create_resp = await client.post("/api/games")
    code = create_resp.json()["code"]

    response = await client.post(
        f"/api/games/{code}/players",
        json={"name": "   "},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_join_name_validation_too_long(client: AsyncClient):
    """Joining with a name longer than 50 chars returns 422."""
    create_resp = await client.post("/api/games")
    code = create_resp.json()["code"]

    response = await client.post(
        f"/api/games/{code}/players",
        json={"name": "A" * 51},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_name_is_trimmed(client: AsyncClient):
    """Leading/trailing whitespace in names is stripped."""
    create_resp = await client.post("/api/games")
    code = create_resp.json()["code"]

    response = await client.post(
        f"/api/games/{code}/players",
        json={"name": "  Alice  "},
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Alice"


@pytest.mark.asyncio
async def test_auth_dependency_valid_token(client: AsyncClient):
    """A valid X-Player-Token header authenticates the player.

    This test doesn't use an auth-protected endpoint yet (those come in
    later phases), so we test the dependency indirectly by verifying the
    token is returned and is the right length.
    """
    create_resp = await client.post("/api/games")
    code = create_resp.json()["code"]

    join_resp = await client.post(
        f"/api/games/{code}/players",
        json={"name": "Alice"},
    )

    token = join_resp.json()["token"]
    assert isinstance(token, str)
    assert len(token) == 64


@pytest.mark.asyncio
async def test_multiple_players_get_unique_tokens(client: AsyncClient):
    """Each player gets a unique token."""
    create_resp = await client.post("/api/games")
    code = create_resp.json()["code"]

    resp1 = await client.post(f"/api/games/{code}/players", json={"name": "Alice"})
    resp2 = await client.post(f"/api/games/{code}/players", json={"name": "Bob"})
    resp3 = await client.post(f"/api/games/{code}/players", json={"name": "Charlie"})

    tokens = {resp1.json()["token"], resp2.json()["token"], resp3.json()["token"]}
    assert len(tokens) == 3  # All unique
