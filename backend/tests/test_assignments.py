"""Tests for game start and kill chain generation (Phase 4).

The kill chain is the heart of the game -- these tests verify:
- Circular chain integrity at various player counts
- Assignment validity (correct rooms/weapons from the game's pools)
- Start-game validation (host-only, minimum players/rooms/weapons)
- Assignment retrieval (each player sees only their own)
"""

import pytest
from httpx import AsyncClient


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


async def add_players(client: AsyncClient, code: str, names: list[str]) -> list[str]:
    """Add multiple players to a game. Returns list of tokens."""
    tokens = []
    for name in names:
        resp = await client.post(
            f"/api/games/{code}/players",
            json={"name": name},
        )
        tokens.append(resp.json()["token"])
    return tokens


async def add_rooms(client: AsyncClient, code: str, token: str, names: list[str]) -> None:
    """Add multiple rooms to a game."""
    for name in names:
        await client.post(
            f"/api/games/{code}/rooms",
            json={"name": name},
            headers={"X-Player-Token": token},
        )


async def add_weapons(client: AsyncClient, code: str, token: str, names: list[str]) -> None:
    """Add multiple weapons to a game."""
    for name in names:
        await client.post(
            f"/api/games/{code}/weapons",
            json={"name": name},
            headers={"X-Player-Token": token},
        )


async def setup_startable_game(
    client: AsyncClient,
    player_names: list[str] | None = None,
    room_names: list[str] | None = None,
    weapon_names: list[str] | None = None,
) -> tuple[str, list[str]]:
    """Create a game ready to start: host + extra players, rooms, weapons.

    Returns (code, [host_token, player2_token, player3_token, ...]).
    The first token is always the host.
    """
    if player_names is None:
        player_names = ["Alice", "Bob", "Charlie"]
    if room_names is None:
        room_names = ["Kitchen", "Bedroom"]
    if weapon_names is None:
        weapon_names = ["Spatula", "Mug"]

    # First player becomes host.
    code, host_token = await create_game_and_join(client, player_names[0])

    # Add remaining players.
    other_tokens = await add_players(client, code, player_names[1:])
    all_tokens = [host_token] + other_tokens

    # Add rooms and weapons (as host).
    await add_rooms(client, code, host_token, room_names)
    await add_weapons(client, code, host_token, weapon_names)

    return code, all_tokens


# ---------------------------------------------------------------------------
# Start game -- success
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_start_game_success(client: AsyncClient):
    """POST /api/games/{code}/start succeeds with 3 players, rooms, weapons."""
    code, tokens = await setup_startable_game(client)
    host_token = tokens[0]

    response = await client.post(
        f"/api/games/{code}/start",
        headers={"X-Player-Token": host_token},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "in_progress"}


@pytest.mark.asyncio
async def test_game_status_changes_to_in_progress(client: AsyncClient):
    """After starting, GET /api/games/{code} shows status as in_progress."""
    code, tokens = await setup_startable_game(client)
    host_token = tokens[0]

    await client.post(
        f"/api/games/{code}/start",
        headers={"X-Player-Token": host_token},
    )

    game_resp = await client.get(f"/api/games/{code}")
    assert game_resp.json()["status"] == "in_progress"


# ---------------------------------------------------------------------------
# Start game -- validation failures
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cannot_start_if_not_host(client: AsyncClient):
    """A non-host player cannot start the game (403)."""
    code, tokens = await setup_startable_game(client)
    non_host_token = tokens[1]  # Bob is not the host

    response = await client.post(
        f"/api/games/{code}/start",
        headers={"X-Player-Token": non_host_token},
    )

    assert response.status_code == 403
    assert "host" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_cannot_start_if_not_in_lobby(client: AsyncClient):
    """Starting an already-started game returns 400."""
    code, tokens = await setup_startable_game(client)
    host_token = tokens[0]

    # Start it once.
    await client.post(
        f"/api/games/{code}/start",
        headers={"X-Player-Token": host_token},
    )

    # Try to start again.
    response = await client.post(
        f"/api/games/{code}/start",
        headers={"X-Player-Token": host_token},
    )

    assert response.status_code == 400
    assert "lobby" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_cannot_start_with_fewer_than_3_players(client: AsyncClient):
    """Starting with only 2 players returns 400."""
    code, host_token = await create_game_and_join(client, "Alice")
    await add_players(client, code, ["Bob"])
    await add_rooms(client, code, host_token, ["Kitchen"])
    await add_weapons(client, code, host_token, ["Spatula"])

    response = await client.post(
        f"/api/games/{code}/start",
        headers={"X-Player-Token": host_token},
    )

    assert response.status_code == 400
    assert "3 players" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_cannot_start_with_0_rooms(client: AsyncClient):
    """Starting with no rooms returns 400."""
    code, host_token = await create_game_and_join(client, "Alice")
    await add_players(client, code, ["Bob", "Charlie"])
    await add_weapons(client, code, host_token, ["Spatula"])

    response = await client.post(
        f"/api/games/{code}/start",
        headers={"X-Player-Token": host_token},
    )

    assert response.status_code == 400
    assert "room" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_cannot_start_with_0_weapons(client: AsyncClient):
    """Starting with no weapons returns 400."""
    code, host_token = await create_game_and_join(client, "Alice")
    await add_players(client, code, ["Bob", "Charlie"])
    await add_rooms(client, code, host_token, ["Kitchen"])

    response = await client.post(
        f"/api/games/{code}/start",
        headers={"X-Player-Token": host_token},
    )

    assert response.status_code == 400
    assert "weapon" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_player_from_different_game_cannot_start(client: AsyncClient):
    """A player from game B cannot start game A (403)."""
    code_a, tokens_a = await setup_startable_game(
        client,
        player_names=["Alice", "Bob", "Charlie"],
    )

    # Create game B with a player.
    code_b, token_b = await create_game_and_join(client, "Dave")

    # Dave tries to start game A.
    response = await client.post(
        f"/api/games/{code_a}/start",
        headers={"X-Player-Token": token_b},
    )

    assert response.status_code == 403
    assert "not a player" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Kill chain integrity -- every player has exactly one assignment
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_every_player_has_one_assignment_after_start(client: AsyncClient):
    """After starting, every player has exactly one active assignment."""
    code, tokens = await setup_startable_game(client)
    host_token = tokens[0]

    await client.post(
        f"/api/games/{code}/start",
        headers={"X-Player-Token": host_token},
    )

    # Every player should be able to retrieve their assignment.
    for token in tokens:
        resp = await client.get(
            f"/api/games/{code}/assignment",
            headers={"X-Player-Token": token},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "target_name" in data
        assert "room_name" in data
        assert "weapon_name" in data


# ---------------------------------------------------------------------------
# Kill chain circularity -- THE critical test
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_kill_chain_is_circular_3_players(client: AsyncClient):
    """With 3 players, following target links forms a cycle visiting all 3."""
    names = ["Alice", "Bob", "Charlie"]
    code, tokens = await setup_startable_game(client, player_names=names)

    await client.post(
        f"/api/games/{code}/start",
        headers={"X-Player-Token": tokens[0]},
    )

    # Build a name->target_name map.
    name_to_target: dict[str, str] = {}
    for i, name in enumerate(names):
        resp = await client.get(
            f"/api/games/{code}/assignment",
            headers={"X-Player-Token": tokens[i]},
        )
        assert resp.status_code == 200
        name_to_target[name] = resp.json()["target_name"]

    # Verify circularity: start at any player, follow targets, must visit
    # all players exactly once and return to start.
    visited = []
    current = names[0]
    for _ in range(len(names)):
        visited.append(current)
        current = name_to_target[current]

    # After following N links, we should be back at the start.
    assert current == names[0], f"Chain did not loop back: ended at {current}"
    assert set(visited) == set(names), f"Not all players visited: {visited}"
    assert len(visited) == len(names), f"Visited wrong count: {visited}"


@pytest.mark.asyncio
async def test_kill_chain_is_circular_5_players(client: AsyncClient):
    """With 5 players, the kill chain is a valid cycle through all 5."""
    names = ["Alice", "Bob", "Charlie", "Dave", "Eve"]
    code, tokens = await setup_startable_game(client, player_names=names)

    await client.post(
        f"/api/games/{code}/start",
        headers={"X-Player-Token": tokens[0]},
    )

    name_to_target: dict[str, str] = {}
    for i, name in enumerate(names):
        resp = await client.get(
            f"/api/games/{code}/assignment",
            headers={"X-Player-Token": tokens[i]},
        )
        assert resp.status_code == 200
        name_to_target[name] = resp.json()["target_name"]

    visited = []
    current = names[0]
    for _ in range(len(names)):
        visited.append(current)
        current = name_to_target[current]

    assert current == names[0], f"Chain did not loop back: ended at {current}"
    assert set(visited) == set(names)
    assert len(visited) == len(names)


@pytest.mark.asyncio
async def test_kill_chain_is_circular_10_players(client: AsyncClient):
    """With 10 players, the kill chain is a valid cycle through all 10."""
    names = [f"Player{i}" for i in range(10)]
    code, tokens = await setup_startable_game(client, player_names=names)

    await client.post(
        f"/api/games/{code}/start",
        headers={"X-Player-Token": tokens[0]},
    )

    name_to_target: dict[str, str] = {}
    for i, name in enumerate(names):
        resp = await client.get(
            f"/api/games/{code}/assignment",
            headers={"X-Player-Token": tokens[i]},
        )
        assert resp.status_code == 200
        name_to_target[name] = resp.json()["target_name"]

    visited = []
    current = names[0]
    for _ in range(len(names)):
        visited.append(current)
        current = name_to_target[current]

    assert current == names[0], f"Chain did not loop back: ended at {current}"
    assert set(visited) == set(names)
    assert len(visited) == len(names)


# ---------------------------------------------------------------------------
# Assignment content validation -- rooms and weapons are from the game's pools
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_assignments_use_valid_rooms_and_weapons(client: AsyncClient):
    """Every assignment references a room and weapon from the game's pools."""
    room_names = ["Kitchen", "Bedroom", "Living Room"]
    weapon_names = ["Spatula", "Mug", "Pillow"]
    names = ["Alice", "Bob", "Charlie", "Dave"]

    code, tokens = await setup_startable_game(
        client,
        player_names=names,
        room_names=room_names,
        weapon_names=weapon_names,
    )

    await client.post(
        f"/api/games/{code}/start",
        headers={"X-Player-Token": tokens[0]},
    )

    for i, name in enumerate(names):
        resp = await client.get(
            f"/api/games/{code}/assignment",
            headers={"X-Player-Token": tokens[i]},
        )
        data = resp.json()
        assert data["room_name"] in room_names, f"{name}'s room '{data['room_name']}' not in pool"
        assert data["weapon_name"] in weapon_names, (
            f"{name}'s weapon '{data['weapon_name']}' not in pool"
        )


@pytest.mark.asyncio
async def test_no_player_targets_themselves(client: AsyncClient):
    """No player should be assigned to kill themselves."""
    names = ["Alice", "Bob", "Charlie", "Dave", "Eve"]
    code, tokens = await setup_startable_game(client, player_names=names)

    await client.post(
        f"/api/games/{code}/start",
        headers={"X-Player-Token": tokens[0]},
    )

    for i, name in enumerate(names):
        resp = await client.get(
            f"/api/games/{code}/assignment",
            headers={"X-Player-Token": tokens[i]},
        )
        assert resp.json()["target_name"] != name, f"{name} is assigned to kill themselves"


# ---------------------------------------------------------------------------
# GET /assignment endpoint
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_assignment_before_game_starts_returns_404(client: AsyncClient):
    """GET /assignment returns 404 when the game hasn't started yet."""
    code, tokens = await setup_startable_game(client)

    resp = await client.get(
        f"/api/games/{code}/assignment",
        headers={"X-Player-Token": tokens[0]},
    )

    assert resp.status_code == 404
    assert "no active assignment" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_each_player_sees_only_their_own_assignment(client: AsyncClient):
    """Different players get different assignments (target names differ when chain > 2)."""
    names = ["Alice", "Bob", "Charlie", "Dave"]
    code, tokens = await setup_startable_game(client, player_names=names)

    await client.post(
        f"/api/games/{code}/start",
        headers={"X-Player-Token": tokens[0]},
    )

    # Collect all assignments.
    assignments = {}
    for i, name in enumerate(names):
        resp = await client.get(
            f"/api/games/{code}/assignment",
            headers={"X-Player-Token": tokens[i]},
        )
        assert resp.status_code == 200
        assignments[name] = resp.json()

    # Each player should have a unique target (in a circular chain,
    # every player is someone's target exactly once).
    targets = [a["target_name"] for a in assignments.values()]
    assert len(set(targets)) == len(targets), f"Duplicate targets found: {targets}"


@pytest.mark.asyncio
async def test_get_assignment_player_from_other_game_returns_403(
    client: AsyncClient,
):
    """A player from game B cannot fetch assignments from game A (403)."""
    code_a, tokens_a = await setup_startable_game(
        client,
        player_names=["Alice", "Bob", "Charlie"],
    )
    await client.post(
        f"/api/games/{code_a}/start",
        headers={"X-Player-Token": tokens_a[0]},
    )

    # Create game B with a player.
    code_b, token_b = await create_game_and_join(client, "Dave")

    # Dave tries to get assignment from game A.
    resp = await client.get(
        f"/api/games/{code_a}/assignment",
        headers={"X-Player-Token": token_b},
    )

    assert resp.status_code == 403
    assert "not a player" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_assignment_missing_token_returns_422(client: AsyncClient):
    """GET /assignment without a token returns 422."""
    code, tokens = await setup_startable_game(client)
    await client.post(
        f"/api/games/{code}/start",
        headers={"X-Player-Token": tokens[0]},
    )

    resp = await client.get(f"/api/games/{code}/assignment")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_assignment_invalid_token_returns_401(client: AsyncClient):
    """GET /assignment with an invalid token returns 401."""
    code, tokens = await setup_startable_game(client)
    await client.post(
        f"/api/games/{code}/start",
        headers={"X-Player-Token": tokens[0]},
    )

    resp = await client.get(
        f"/api/games/{code}/assignment",
        headers={"X-Player-Token": "totally-invalid-token"},
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Start game -- auth edge cases
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_start_game_missing_token_returns_422(client: AsyncClient):
    """POST /start without a token returns 422."""
    code, tokens = await setup_startable_game(client)

    resp = await client.post(f"/api/games/{code}/start")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_start_game_invalid_token_returns_401(client: AsyncClient):
    """POST /start with an invalid token returns 401."""
    code, tokens = await setup_startable_game(client)

    resp = await client.post(
        f"/api/games/{code}/start",
        headers={"X-Player-Token": "bad-token"},
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Kill chain with minimum requirements (exactly 3 players, 1 room, 1 weapon)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_start_with_exactly_3_players_1_room_1_weapon(client: AsyncClient):
    """The absolute minimum: 3 players, 1 room, 1 weapon -- should work."""
    code, tokens = await setup_startable_game(
        client,
        player_names=["Alice", "Bob", "Charlie"],
        room_names=["Kitchen"],
        weapon_names=["Spatula"],
    )

    resp = await client.post(
        f"/api/games/{code}/start",
        headers={"X-Player-Token": tokens[0]},
    )
    assert resp.status_code == 200

    # All assignments should reference the single room and weapon.
    for token in tokens:
        a_resp = await client.get(
            f"/api/games/{code}/assignment",
            headers={"X-Player-Token": token},
        )
        data = a_resp.json()
        assert data["room_name"] == "Kitchen"
        assert data["weapon_name"] == "Spatula"

    # Chain should still be circular.
    name_to_target: dict[str, str] = {}
    names = ["Alice", "Bob", "Charlie"]
    for i, name in enumerate(names):
        a_resp = await client.get(
            f"/api/games/{code}/assignment",
            headers={"X-Player-Token": tokens[i]},
        )
        name_to_target[name] = a_resp.json()["target_name"]

    visited = []
    current = names[0]
    for _ in range(len(names)):
        visited.append(current)
        current = name_to_target[current]

    assert current == names[0]
    assert set(visited) == set(names)
