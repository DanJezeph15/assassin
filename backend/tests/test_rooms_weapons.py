"""Tests for rooms and weapons CRUD endpoints (Phase 3)."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def create_game_and_join(client: AsyncClient, player_name: str = "Alice"):
    """Create a game, join as a player, return (code, token)."""
    create_resp = await client.post("/api/games")
    code = create_resp.json()["code"]

    join_resp = await client.post(
        f"/api/games/{code}/players",
        json={"name": player_name},
    )
    token = join_resp.json()["token"]

    return code, token


# ---------------------------------------------------------------------------
# Room tests -- adding
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_add_room(client: AsyncClient):
    """POST /api/games/{code}/rooms creates a room and returns 201."""
    code, token = await create_game_and_join(client)

    response = await client.post(
        f"/api/games/{code}/rooms",
        json={"name": "Kitchen"},
        headers={"X-Player-Token": token},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Kitchen"
    assert "id" in data


@pytest.mark.asyncio
async def test_add_room_strips_whitespace(client: AsyncClient):
    """Room names are trimmed of leading/trailing whitespace."""
    code, token = await create_game_and_join(client)

    response = await client.post(
        f"/api/games/{code}/rooms",
        json={"name": "  Living Room  "},
        headers={"X-Player-Token": token},
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Living Room"


@pytest.mark.asyncio
async def test_room_appears_in_game_detail(client: AsyncClient):
    """Rooms added via POST appear in GET /api/games/{code} response."""
    code, token = await create_game_and_join(client)

    await client.post(
        f"/api/games/{code}/rooms",
        json={"name": "Kitchen"},
        headers={"X-Player-Token": token},
    )
    await client.post(
        f"/api/games/{code}/rooms",
        json={"name": "Bedroom"},
        headers={"X-Player-Token": token},
    )

    game_resp = await client.get(f"/api/games/{code}")
    data = game_resp.json()

    room_names = {r["name"] for r in data["rooms"]}
    assert room_names == {"Kitchen", "Bedroom"}


@pytest.mark.asyncio
async def test_duplicate_room_name_rejected(client: AsyncClient):
    """Adding a room with an exact duplicate name returns 400."""
    code, token = await create_game_and_join(client)

    await client.post(
        f"/api/games/{code}/rooms",
        json={"name": "Kitchen"},
        headers={"X-Player-Token": token},
    )

    response = await client.post(
        f"/api/games/{code}/rooms",
        json={"name": "Kitchen"},
        headers={"X-Player-Token": token},
    )

    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_duplicate_room_name_case_insensitive(client: AsyncClient):
    """Room name uniqueness check is case-insensitive."""
    code, token = await create_game_and_join(client)

    await client.post(
        f"/api/games/{code}/rooms",
        json={"name": "Kitchen"},
        headers={"X-Player-Token": token},
    )

    response = await client.post(
        f"/api/games/{code}/rooms",
        json={"name": "kitchen"},
        headers={"X-Player-Token": token},
    )

    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_cannot_add_room_when_not_in_lobby(client: AsyncClient, db: AsyncSession):
    """Adding a room to a game not in LOBBY status returns 400."""
    from app.models.game import Game, GameStatus
    from app.models.player import Player
    import secrets

    # Create an in-progress game directly in the DB.
    game = Game(code="INPROG", status=GameStatus.IN_PROGRESS)
    db.add(game)
    await db.flush()

    player = Player(game_id=game.id, name="Alice", token=secrets.token_hex(32))
    db.add(player)
    await db.flush()

    game.host_id = player.id
    await db.commit()

    response = await client.post(
        "/api/games/INPROG/rooms",
        json={"name": "Kitchen"},
        headers={"X-Player-Token": player.token},
    )

    assert response.status_code == 400
    assert "lobby" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_add_room_empty_name_rejected(client: AsyncClient):
    """An empty room name returns 422."""
    code, token = await create_game_and_join(client)

    response = await client.post(
        f"/api/games/{code}/rooms",
        json={"name": ""},
        headers={"X-Player-Token": token},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_add_room_whitespace_only_name_rejected(client: AsyncClient):
    """A whitespace-only room name returns 422."""
    code, token = await create_game_and_join(client)

    response = await client.post(
        f"/api/games/{code}/rooms",
        json={"name": "   "},
        headers={"X-Player-Token": token},
    )

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Room tests -- removing
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_remove_room(client: AsyncClient):
    """DELETE /api/games/{code}/rooms/{room_id} removes a room and returns 204."""
    code, token = await create_game_and_join(client)

    add_resp = await client.post(
        f"/api/games/{code}/rooms",
        json={"name": "Kitchen"},
        headers={"X-Player-Token": token},
    )
    room_id = add_resp.json()["id"]

    response = await client.delete(
        f"/api/games/{code}/rooms/{room_id}",
        headers={"X-Player-Token": token},
    )

    assert response.status_code == 204

    # Verify it's gone from game details.
    game_resp = await client.get(f"/api/games/{code}")
    assert len(game_resp.json()["rooms"]) == 0


@pytest.mark.asyncio
async def test_remove_room_not_in_game(client: AsyncClient):
    """Removing a room that doesn't belong to this game returns 404."""
    code, token = await create_game_and_join(client)

    fake_room_id = str(uuid.uuid4())

    response = await client.delete(
        f"/api/games/{code}/rooms/{fake_room_id}",
        headers={"X-Player-Token": token},
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_remove_room_from_different_game(client: AsyncClient):
    """A room from game A cannot be removed via game B's endpoint."""
    # Create game A and add a room.
    code_a, token_a = await create_game_and_join(client, "Alice")
    add_resp = await client.post(
        f"/api/games/{code_a}/rooms",
        json={"name": "Kitchen"},
        headers={"X-Player-Token": token_a},
    )
    room_id = add_resp.json()["id"]

    # Create game B.
    code_b, token_b = await create_game_and_join(client, "Bob")

    # Try to remove game A's room via game B.
    response = await client.delete(
        f"/api/games/{code_b}/rooms/{room_id}",
        headers={"X-Player-Token": token_b},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cannot_remove_room_when_not_in_lobby(
    client: AsyncClient, db: AsyncSession
):
    """Removing a room from a game not in LOBBY status returns 400."""
    from app.models.game import Game, GameStatus
    from app.models.player import Player
    from app.models.room import Room
    import secrets

    game = Game(code="RMROOM", status=GameStatus.IN_PROGRESS)
    db.add(game)
    await db.flush()

    player = Player(game_id=game.id, name="Alice", token=secrets.token_hex(32))
    db.add(player)
    await db.flush()

    game.host_id = player.id

    room = Room(game_id=game.id, name="Kitchen")
    db.add(room)
    await db.commit()
    await db.refresh(room)

    response = await client.delete(
        f"/api/games/RMROOM/rooms/{room.id}",
        headers={"X-Player-Token": player.token},
    )

    assert response.status_code == 400
    assert "lobby" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Weapon tests -- adding
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_add_weapon(client: AsyncClient):
    """POST /api/games/{code}/weapons creates a weapon and returns 201."""
    code, token = await create_game_and_join(client)

    response = await client.post(
        f"/api/games/{code}/weapons",
        json={"name": "Spatula"},
        headers={"X-Player-Token": token},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Spatula"
    assert "id" in data


@pytest.mark.asyncio
async def test_add_weapon_strips_whitespace(client: AsyncClient):
    """Weapon names are trimmed of leading/trailing whitespace."""
    code, token = await create_game_and_join(client)

    response = await client.post(
        f"/api/games/{code}/weapons",
        json={"name": "  Rubber Duck  "},
        headers={"X-Player-Token": token},
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Rubber Duck"


@pytest.mark.asyncio
async def test_weapon_appears_in_game_detail(client: AsyncClient):
    """Weapons added via POST appear in GET /api/games/{code} response."""
    code, token = await create_game_and_join(client)

    await client.post(
        f"/api/games/{code}/weapons",
        json={"name": "Spatula"},
        headers={"X-Player-Token": token},
    )
    await client.post(
        f"/api/games/{code}/weapons",
        json={"name": "Mug"},
        headers={"X-Player-Token": token},
    )

    game_resp = await client.get(f"/api/games/{code}")
    data = game_resp.json()

    weapon_names = {w["name"] for w in data["weapons"]}
    assert weapon_names == {"Spatula", "Mug"}


@pytest.mark.asyncio
async def test_duplicate_weapon_name_rejected(client: AsyncClient):
    """Adding a weapon with an exact duplicate name returns 400."""
    code, token = await create_game_and_join(client)

    await client.post(
        f"/api/games/{code}/weapons",
        json={"name": "Spatula"},
        headers={"X-Player-Token": token},
    )

    response = await client.post(
        f"/api/games/{code}/weapons",
        json={"name": "Spatula"},
        headers={"X-Player-Token": token},
    )

    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_duplicate_weapon_name_case_insensitive(client: AsyncClient):
    """Weapon name uniqueness check is case-insensitive."""
    code, token = await create_game_and_join(client)

    await client.post(
        f"/api/games/{code}/weapons",
        json={"name": "Spatula"},
        headers={"X-Player-Token": token},
    )

    response = await client.post(
        f"/api/games/{code}/weapons",
        json={"name": "spatula"},
        headers={"X-Player-Token": token},
    )

    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_cannot_add_weapon_when_not_in_lobby(
    client: AsyncClient, db: AsyncSession
):
    """Adding a weapon to a game not in LOBBY status returns 400."""
    from app.models.game import Game, GameStatus
    from app.models.player import Player
    import secrets

    game = Game(code="WPNLOB", status=GameStatus.IN_PROGRESS)
    db.add(game)
    await db.flush()

    player = Player(game_id=game.id, name="Alice", token=secrets.token_hex(32))
    db.add(player)
    await db.flush()

    game.host_id = player.id
    await db.commit()

    response = await client.post(
        "/api/games/WPNLOB/weapons",
        json={"name": "Spatula"},
        headers={"X-Player-Token": player.token},
    )

    assert response.status_code == 400
    assert "lobby" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_add_weapon_empty_name_rejected(client: AsyncClient):
    """An empty weapon name returns 422."""
    code, token = await create_game_and_join(client)

    response = await client.post(
        f"/api/games/{code}/weapons",
        json={"name": ""},
        headers={"X-Player-Token": token},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_add_weapon_whitespace_only_name_rejected(client: AsyncClient):
    """A whitespace-only weapon name returns 422."""
    code, token = await create_game_and_join(client)

    response = await client.post(
        f"/api/games/{code}/weapons",
        json={"name": "   "},
        headers={"X-Player-Token": token},
    )

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Weapon tests -- removing
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_remove_weapon(client: AsyncClient):
    """DELETE /api/games/{code}/weapons/{weapon_id} removes a weapon and returns 204."""
    code, token = await create_game_and_join(client)

    add_resp = await client.post(
        f"/api/games/{code}/weapons",
        json={"name": "Spatula"},
        headers={"X-Player-Token": token},
    )
    weapon_id = add_resp.json()["id"]

    response = await client.delete(
        f"/api/games/{code}/weapons/{weapon_id}",
        headers={"X-Player-Token": token},
    )

    assert response.status_code == 204

    # Verify it's gone from game details.
    game_resp = await client.get(f"/api/games/{code}")
    assert len(game_resp.json()["weapons"]) == 0


@pytest.mark.asyncio
async def test_remove_weapon_not_in_game(client: AsyncClient):
    """Removing a weapon that doesn't belong to this game returns 404."""
    code, token = await create_game_and_join(client)

    fake_weapon_id = str(uuid.uuid4())

    response = await client.delete(
        f"/api/games/{code}/weapons/{fake_weapon_id}",
        headers={"X-Player-Token": token},
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_remove_weapon_from_different_game(client: AsyncClient):
    """A weapon from game A cannot be removed via game B's endpoint."""
    # Create game A and add a weapon.
    code_a, token_a = await create_game_and_join(client, "Alice")
    add_resp = await client.post(
        f"/api/games/{code_a}/weapons",
        json={"name": "Spatula"},
        headers={"X-Player-Token": token_a},
    )
    weapon_id = add_resp.json()["id"]

    # Create game B.
    code_b, token_b = await create_game_and_join(client, "Bob")

    # Try to remove game A's weapon via game B.
    response = await client.delete(
        f"/api/games/{code_b}/weapons/{weapon_id}",
        headers={"X-Player-Token": token_b},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cannot_remove_weapon_when_not_in_lobby(
    client: AsyncClient, db: AsyncSession
):
    """Removing a weapon from a game not in LOBBY status returns 400."""
    from app.models.game import Game, GameStatus
    from app.models.player import Player
    from app.models.weapon import Weapon
    import secrets

    game = Game(code="RMWPN1", status=GameStatus.IN_PROGRESS)
    db.add(game)
    await db.flush()

    player = Player(game_id=game.id, name="Alice", token=secrets.token_hex(32))
    db.add(player)
    await db.flush()

    game.host_id = player.id

    weapon = Weapon(game_id=game.id, name="Spatula")
    db.add(weapon)
    await db.commit()
    await db.refresh(weapon)

    response = await client.delete(
        f"/api/games/RMWPN1/weapons/{weapon.id}",
        headers={"X-Player-Token": player.token},
    )

    assert response.status_code == 400
    assert "lobby" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Cross-game authorization tests -- player must belong to the game
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_player_from_other_game_cannot_add_room(client: AsyncClient):
    """A player from Game A cannot add a room to Game B (403)."""
    code_a, token_a = await create_game_and_join(client, "Alice")
    code_b, token_b = await create_game_and_join(client, "Bob")

    response = await client.post(
        f"/api/games/{code_b}/rooms",
        json={"name": "Kitchen"},
        headers={"X-Player-Token": token_a},
    )

    assert response.status_code == 403
    assert "not a player" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_player_from_other_game_cannot_add_weapon(client: AsyncClient):
    """A player from Game A cannot add a weapon to Game B (403)."""
    code_a, token_a = await create_game_and_join(client, "Alice")
    code_b, token_b = await create_game_and_join(client, "Bob")

    response = await client.post(
        f"/api/games/{code_b}/weapons",
        json={"name": "Spatula"},
        headers={"X-Player-Token": token_a},
    )

    assert response.status_code == 403
    assert "not a player" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_player_from_other_game_cannot_delete_room(client: AsyncClient):
    """A player from Game A cannot delete a room from Game B (403)."""
    code_a, token_a = await create_game_and_join(client, "Alice")
    code_b, token_b = await create_game_and_join(client, "Bob")

    # Add a room to Game B.
    add_resp = await client.post(
        f"/api/games/{code_b}/rooms",
        json={"name": "Kitchen"},
        headers={"X-Player-Token": token_b},
    )
    room_id = add_resp.json()["id"]

    # Player A tries to delete Game B's room.
    response = await client.delete(
        f"/api/games/{code_b}/rooms/{room_id}",
        headers={"X-Player-Token": token_a},
    )

    assert response.status_code == 403
    assert "not a player" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_player_from_other_game_cannot_delete_weapon(client: AsyncClient):
    """A player from Game A cannot delete a weapon from Game B (403)."""
    code_a, token_a = await create_game_and_join(client, "Alice")
    code_b, token_b = await create_game_and_join(client, "Bob")

    # Add a weapon to Game B.
    add_resp = await client.post(
        f"/api/games/{code_b}/weapons",
        json={"name": "Spatula"},
        headers={"X-Player-Token": token_b},
    )
    weapon_id = add_resp.json()["id"]

    # Player A tries to delete Game B's weapon.
    response = await client.delete(
        f"/api/games/{code_b}/weapons/{weapon_id}",
        headers={"X-Player-Token": token_a},
    )

    assert response.status_code == 403
    assert "not a player" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Auth tests -- rooms and weapons require a valid player token
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_add_room_missing_token(client: AsyncClient):
    """Adding a room without a token returns 422 (missing header)."""
    create_resp = await client.post("/api/games")
    code = create_resp.json()["code"]

    response = await client.post(
        f"/api/games/{code}/rooms",
        json={"name": "Kitchen"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_add_room_invalid_token(client: AsyncClient):
    """Adding a room with an invalid token returns 401."""
    create_resp = await client.post("/api/games")
    code = create_resp.json()["code"]

    response = await client.post(
        f"/api/games/{code}/rooms",
        json={"name": "Kitchen"},
        headers={"X-Player-Token": "invalid-token-value"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_remove_room_missing_token(client: AsyncClient):
    """Removing a room without a token returns 422."""
    code, token = await create_game_and_join(client)

    add_resp = await client.post(
        f"/api/games/{code}/rooms",
        json={"name": "Kitchen"},
        headers={"X-Player-Token": token},
    )
    room_id = add_resp.json()["id"]

    response = await client.delete(f"/api/games/{code}/rooms/{room_id}")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_remove_room_invalid_token(client: AsyncClient):
    """Removing a room with an invalid token returns 401."""
    code, token = await create_game_and_join(client)

    add_resp = await client.post(
        f"/api/games/{code}/rooms",
        json={"name": "Kitchen"},
        headers={"X-Player-Token": token},
    )
    room_id = add_resp.json()["id"]

    response = await client.delete(
        f"/api/games/{code}/rooms/{room_id}",
        headers={"X-Player-Token": "invalid-token-value"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_add_weapon_missing_token(client: AsyncClient):
    """Adding a weapon without a token returns 422."""
    create_resp = await client.post("/api/games")
    code = create_resp.json()["code"]

    response = await client.post(
        f"/api/games/{code}/weapons",
        json={"name": "Spatula"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_add_weapon_invalid_token(client: AsyncClient):
    """Adding a weapon with an invalid token returns 401."""
    create_resp = await client.post("/api/games")
    code = create_resp.json()["code"]

    response = await client.post(
        f"/api/games/{code}/weapons",
        json={"name": "Spatula"},
        headers={"X-Player-Token": "invalid-token-value"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_remove_weapon_missing_token(client: AsyncClient):
    """Removing a weapon without a token returns 422."""
    code, token = await create_game_and_join(client)

    add_resp = await client.post(
        f"/api/games/{code}/weapons",
        json={"name": "Spatula"},
        headers={"X-Player-Token": token},
    )
    weapon_id = add_resp.json()["id"]

    response = await client.delete(f"/api/games/{code}/weapons/{weapon_id}")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_remove_weapon_invalid_token(client: AsyncClient):
    """Removing a weapon with an invalid token returns 401."""
    code, token = await create_game_and_join(client)

    add_resp = await client.post(
        f"/api/games/{code}/weapons",
        json={"name": "Spatula"},
        headers={"X-Player-Token": token},
    )
    weapon_id = add_resp.json()["id"]

    response = await client.delete(
        f"/api/games/{code}/weapons/{weapon_id}",
        headers={"X-Player-Token": "invalid-token-value"},
    )

    assert response.status_code == 401
