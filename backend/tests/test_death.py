"""Tests for death processing and kill chain inheritance (Phase 5).

The kill chain inheritance is the most critical game mechanic. These tests verify:
- Single death: victim dies, killer inherits victim's assignment
- Sequential deaths through a full game to completion
- Chain integrity after each death (remaining alive players form a valid ring)
- Game over detection when 1 player remains
- Leaderboard accuracy and sorting
- Edge cases: dead player can't die again, wrong game status, wrong game
"""

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Helpers (mirrors test_assignments.py patterns)
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

    Returns (code, [host_token, player2_token, ...]).
    The first token is always the host.
    """
    if player_names is None:
        player_names = ["Alice", "Bob", "Charlie"]
    if room_names is None:
        room_names = ["Kitchen", "Bedroom"]
    if weapon_names is None:
        weapon_names = ["Spatula", "Mug"]

    code, host_token = await create_game_and_join(client, player_names[0])
    other_tokens = await add_players(client, code, player_names[1:])
    all_tokens = [host_token] + other_tokens

    await add_rooms(client, code, host_token, room_names)
    await add_weapons(client, code, host_token, weapon_names)

    return code, all_tokens


async def start_game(client: AsyncClient, code: str, host_token: str) -> None:
    """Start a game. Asserts success."""
    resp = await client.post(
        f"/api/games/{code}/start",
        headers={"X-Player-Token": host_token},
    )
    assert resp.status_code == 200


async def get_assignment_map(
    client: AsyncClient, code: str, names: list[str], tokens: list[str]
) -> dict[str, dict]:
    """Build a name -> assignment dict for all players.

    Returns {name: {"target_name": ..., "room_name": ..., "weapon_name": ...}}.
    Only includes players who have an active assignment (alive players).
    """
    assignments = {}
    for name, token in zip(names, tokens):
        resp = await client.get(
            f"/api/games/{code}/assignment",
            headers={"X-Player-Token": token},
        )
        if resp.status_code == 200:
            assignments[name] = resp.json()
    return assignments


def verify_chain_circularity(assignments: dict[str, dict], expected_names: list[str]) -> None:
    """Verify that the assignment map forms a valid circular chain.

    Walks the chain from the first expected name, verifying we visit all
    expected names exactly once and return to the start.
    """
    assert len(assignments) == len(expected_names), (
        f"Expected {len(expected_names)} assignments, got {len(assignments)}: "
        f"expected={expected_names}, got={list(assignments.keys())}"
    )

    visited = []
    current = expected_names[0]
    for _ in range(len(expected_names)):
        assert current in assignments, f"{current} has no assignment"
        visited.append(current)
        current = assignments[current]["target_name"]

    assert current == expected_names[0], (
        f"Chain did not loop back: ended at {current}, expected {expected_names[0]}"
    )
    assert set(visited) == set(expected_names), (
        f"Not all players visited: visited={visited}, expected={expected_names}"
    )


async def confirm_death(client: AsyncClient, code: str, victim_token: str) -> dict:
    """Have a player confirm their death. Returns the response JSON."""
    resp = await client.post(
        f"/api/games/{code}/deaths",
        headers={"X-Player-Token": victim_token},
    )
    assert resp.status_code == 200, f"Death failed: {resp.json()}"
    return resp.json()


# ---------------------------------------------------------------------------
# Single death -- basic chain inheritance
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_single_death_marks_player_dead(client: AsyncClient):
    """After confirming death, the victim is marked as dead in game state."""
    names = ["Alice", "Bob", "Charlie"]
    code, tokens = await setup_startable_game(client, player_names=names)
    await start_game(client, code, tokens[0])

    # Build assignment map to find who targets whom.
    assignments = await get_assignment_map(client, code, names, tokens)

    # Find who Alice is targeting, and have that person die.
    victim_name = assignments["Alice"]["target_name"]
    victim_idx = names.index(victim_name)
    victim_token = tokens[victim_idx]

    await confirm_death(client, code, victim_token)

    # Check game state -- victim should be dead.
    game_resp = await client.get(f"/api/games/{code}")
    game_data = game_resp.json()
    player_states = {p["name"]: p for p in game_data["players"]}
    assert player_states[victim_name]["is_alive"] is False


@pytest.mark.asyncio
async def test_single_death_increments_killer_kills(client: AsyncClient):
    """The killer's kill count increases by 1 after their target dies."""
    names = ["Alice", "Bob", "Charlie"]
    code, tokens = await setup_startable_game(client, player_names=names)
    await start_game(client, code, tokens[0])

    assignments = await get_assignment_map(client, code, names, tokens)

    # Find Alice's target and have them die.
    victim_name = assignments["Alice"]["target_name"]
    victim_idx = names.index(victim_name)

    death_result = await confirm_death(client, code, tokens[victim_idx])

    assert death_result["killer_name"] == "Alice"
    assert death_result["kill_count"] == 1

    # Verify via game state.
    game_resp = await client.get(f"/api/games/{code}")
    player_states = {p["name"]: p for p in game_resp.json()["players"]}
    assert player_states["Alice"]["kills"] == 1


@pytest.mark.asyncio
async def test_single_death_killer_inherits_victim_assignment(client: AsyncClient):
    """After a death, the killer's new assignment has the victim's old target, room, weapon."""
    names = ["Alice", "Bob", "Charlie"]
    code, tokens = await setup_startable_game(client, player_names=names)
    await start_game(client, code, tokens[0])

    assignments = await get_assignment_map(client, code, names, tokens)

    # Find Alice's target.
    victim_name = assignments["Alice"]["target_name"]
    victim_idx = names.index(victim_name)

    # Record the victim's assignment BEFORE death (what the victim was supposed
    # to do -- this should be inherited by the killer).
    victim_old_assignment = assignments[victim_name]

    await confirm_death(client, code, tokens[victim_idx])

    # Alice should now have a new assignment inheriting from the victim.
    alice_resp = await client.get(
        f"/api/games/{code}/assignment",
        headers={"X-Player-Token": tokens[0]},
    )
    assert alice_resp.status_code == 200
    alice_new = alice_resp.json()

    assert alice_new["target_name"] == victim_old_assignment["target_name"]
    assert alice_new["room_name"] == victim_old_assignment["room_name"]
    assert alice_new["weapon_name"] == victim_old_assignment["weapon_name"]


@pytest.mark.asyncio
async def test_single_death_victim_has_no_active_assignment(client: AsyncClient):
    """After dying, the victim has no active assignment (returns 404)."""
    names = ["Alice", "Bob", "Charlie"]
    code, tokens = await setup_startable_game(client, player_names=names)
    await start_game(client, code, tokens[0])

    assignments = await get_assignment_map(client, code, names, tokens)
    victim_name = assignments["Alice"]["target_name"]
    victim_idx = names.index(victim_name)

    await confirm_death(client, code, tokens[victim_idx])

    # Victim should have no active assignment.
    resp = await client.get(
        f"/api/games/{code}/assignment",
        headers={"X-Player-Token": tokens[victim_idx]},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_single_death_does_not_end_game_with_3_players(client: AsyncClient):
    """With 3 players, 1 death leaves 2 alive -- game is NOT over."""
    names = ["Alice", "Bob", "Charlie"]
    code, tokens = await setup_startable_game(client, player_names=names)
    await start_game(client, code, tokens[0])

    assignments = await get_assignment_map(client, code, names, tokens)
    victim_name = assignments["Alice"]["target_name"]
    victim_idx = names.index(victim_name)

    death_result = await confirm_death(client, code, tokens[victim_idx])

    assert death_result["game_over"] is False
    assert death_result["winner_name"] is None

    # Game should still be in_progress.
    game_resp = await client.get(f"/api/games/{code}")
    assert game_resp.json()["status"] == "in_progress"


# ---------------------------------------------------------------------------
# Chain integrity after deaths
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_chain_intact_after_one_death_3_players(client: AsyncClient):
    """After 1 death with 3 players, the 2 remaining form a valid circular chain."""
    names = ["Alice", "Bob", "Charlie"]
    code, tokens = await setup_startable_game(client, player_names=names)
    await start_game(client, code, tokens[0])

    assignments = await get_assignment_map(client, code, names, tokens)
    victim_name = assignments["Alice"]["target_name"]
    victim_idx = names.index(victim_name)

    await confirm_death(client, code, tokens[victim_idx])

    # Get assignments for surviving players.
    alive_names = [n for n in names if n != victim_name]
    alive_tokens = [t for n, t in zip(names, tokens) if n != victim_name]

    surviving_assignments = await get_assignment_map(client, code, alive_names, alive_tokens)

    verify_chain_circularity(surviving_assignments, alive_names)


@pytest.mark.asyncio
async def test_chain_intact_after_one_death_5_players(client: AsyncClient):
    """After 1 death with 5 players, the 4 remaining form a valid circular chain."""
    names = ["Alice", "Bob", "Charlie", "Dave", "Eve"]
    code, tokens = await setup_startable_game(client, player_names=names)
    await start_game(client, code, tokens[0])

    assignments = await get_assignment_map(client, code, names, tokens)

    # Kill whoever Alice targets.
    victim_name = assignments["Alice"]["target_name"]
    victim_idx = names.index(victim_name)
    await confirm_death(client, code, tokens[victim_idx])

    alive_names = [n for n in names if n != victim_name]
    alive_tokens = [t for n, t in zip(names, tokens) if n != victim_name]

    surviving_assignments = await get_assignment_map(client, code, alive_names, alive_tokens)

    verify_chain_circularity(surviving_assignments, alive_names)


# ---------------------------------------------------------------------------
# Sequential deaths through a full game
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_full_game_3_players(client: AsyncClient):
    """Play a full game with 3 players -- 2 deaths, 1 winner."""
    names = ["Alice", "Bob", "Charlie"]
    code, tokens = await setup_startable_game(client, player_names=names)
    await start_game(client, code, tokens[0])

    name_to_token = dict(zip(names, tokens))
    alive = list(names)

    # Death 1: follow the chain -- find who the first player targets, kill them.
    assignments = await get_assignment_map(client, code, alive, [name_to_token[n] for n in alive])
    victim1 = assignments[alive[0]]["target_name"]
    death1 = await confirm_death(client, code, name_to_token[victim1])

    assert death1["game_over"] is False
    assert death1["kill_count"] == 1
    alive.remove(victim1)

    # Verify chain still intact.
    assignments = await get_assignment_map(client, code, alive, [name_to_token[n] for n in alive])
    verify_chain_circularity(assignments, alive)

    # Death 2: kill the remaining target.
    victim2 = assignments[alive[0]]["target_name"]
    death2 = await confirm_death(client, code, name_to_token[victim2])

    assert death2["game_over"] is True
    assert death2["winner_name"] is not None
    alive.remove(victim2)

    # The winner is the last alive player.
    assert death2["winner_name"] == alive[0]

    # Game status should be FINISHED.
    game_resp = await client.get(f"/api/games/{code}")
    assert game_resp.json()["status"] == "finished"

    # Winner should have no active assignment after game over.
    winner_token = name_to_token[alive[0]]
    resp = await client.get(
        f"/api/games/{code}/assignment",
        headers={"X-Player-Token": winner_token},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_full_game_5_players(client: AsyncClient):
    """Play a full game with 5 players. Verify chain stays correct after every death."""
    names = ["Alice", "Bob", "Charlie", "Dave", "Eve"]
    code, tokens = await setup_startable_game(client, player_names=names)
    await start_game(client, code, tokens[0])

    name_to_token = dict(zip(names, tokens))
    alive = list(names)

    # Kill players one by one following the chain.
    for death_num in range(4):  # 5 players -> 4 deaths -> 1 winner
        assignments = await get_assignment_map(
            client, code, alive, [name_to_token[n] for n in alive]
        )
        verify_chain_circularity(assignments, alive)

        # Pick the first alive player's target to kill.
        victim = assignments[alive[0]]["target_name"]
        result = await confirm_death(client, code, name_to_token[victim])

        alive.remove(victim)

        if death_num < 3:
            assert result["game_over"] is False
        else:
            # Last death -- game over.
            assert result["game_over"] is True
            assert result["winner_name"] == alive[0]

    # Verify final state.
    game_resp = await client.get(f"/api/games/{code}")
    game_data = game_resp.json()
    assert game_data["status"] == "finished"

    alive_players = [p for p in game_data["players"] if p["is_alive"]]
    assert len(alive_players) == 1
    assert alive_players[0]["name"] == alive[0]


@pytest.mark.asyncio
async def test_full_game_10_players(client: AsyncClient):
    """Play a full game with 10 players, verifying chain at every step."""
    names = [f"Player{i}" for i in range(10)]
    code, tokens = await setup_startable_game(client, player_names=names)
    await start_game(client, code, tokens[0])

    name_to_token = dict(zip(names, tokens))
    alive = list(names)
    total_kills: dict[str, int] = {n: 0 for n in names}

    for death_num in range(9):  # 10 players -> 9 deaths
        assignments = await get_assignment_map(
            client, code, alive, [name_to_token[n] for n in alive]
        )
        verify_chain_circularity(assignments, alive)

        # Pick first alive player's target to die.
        killer_name = alive[0]
        victim = assignments[killer_name]["target_name"]
        result = await confirm_death(client, code, name_to_token[victim])

        assert result["killer_name"] == killer_name
        total_kills[killer_name] += 1
        assert result["kill_count"] == total_kills[killer_name]

        alive.remove(victim)

        if death_num < 8:
            assert result["game_over"] is False
        else:
            assert result["game_over"] is True
            assert result["winner_name"] == alive[0]

    game_resp = await client.get(f"/api/games/{code}")
    assert game_resp.json()["status"] == "finished"


# ---------------------------------------------------------------------------
# Game over detection
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_game_over_exactly_when_one_remains(client: AsyncClient):
    """With 3 players: 1st death -> not over, 2nd death -> over."""
    names = ["Alice", "Bob", "Charlie"]
    code, tokens = await setup_startable_game(client, player_names=names)
    await start_game(client, code, tokens[0])

    name_to_token = dict(zip(names, tokens))
    alive = list(names)

    # Death 1: 3 -> 2 alive. NOT game over.
    assignments = await get_assignment_map(client, code, alive, [name_to_token[n] for n in alive])
    victim1 = assignments[alive[0]]["target_name"]
    result1 = await confirm_death(client, code, name_to_token[victim1])
    assert result1["game_over"] is False
    alive.remove(victim1)

    game_resp = await client.get(f"/api/games/{code}")
    assert game_resp.json()["status"] == "in_progress"

    # Death 2: 2 -> 1 alive. Game over.
    assignments = await get_assignment_map(client, code, alive, [name_to_token[n] for n in alive])
    victim2 = assignments[alive[0]]["target_name"]
    result2 = await confirm_death(client, code, name_to_token[victim2])
    assert result2["game_over"] is True
    alive.remove(victim2)
    assert result2["winner_name"] == alive[0]

    game_resp = await client.get(f"/api/games/{code}")
    assert game_resp.json()["status"] == "finished"


# ---------------------------------------------------------------------------
# Leaderboard
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_leaderboard_sorted_by_kills_desc(client: AsyncClient):
    """Leaderboard returns players sorted by kills descending."""
    names = ["Alice", "Bob", "Charlie", "Dave"]
    code, tokens = await setup_startable_game(client, player_names=names)
    await start_game(client, code, tokens[0])

    name_to_token = dict(zip(names, tokens))
    alive = list(names)

    # Kill one player so someone has kills > 0.
    assignments = await get_assignment_map(client, code, alive, [name_to_token[n] for n in alive])
    killer_name = alive[0]
    victim = assignments[killer_name]["target_name"]
    await confirm_death(client, code, name_to_token[victim])
    alive.remove(victim)

    # Check leaderboard.
    resp = await client.get(
        f"/api/games/{code}/leaderboard",
        headers={"X-Player-Token": tokens[0]},
    )
    assert resp.status_code == 200
    leaderboard = resp.json()

    assert len(leaderboard) == len(names)

    # First entry should be the killer with 1 kill.
    assert leaderboard[0]["name"] == killer_name
    assert leaderboard[0]["kills"] == 1
    assert leaderboard[0]["is_alive"] is True

    # Kills should be non-increasing.
    kills = [entry["kills"] for entry in leaderboard]
    assert kills == sorted(kills, reverse=True)


@pytest.mark.asyncio
async def test_leaderboard_includes_dead_players(client: AsyncClient):
    """Dead players appear in the leaderboard with is_alive=False."""
    names = ["Alice", "Bob", "Charlie"]
    code, tokens = await setup_startable_game(client, player_names=names)
    await start_game(client, code, tokens[0])

    name_to_token = dict(zip(names, tokens))
    alive = list(names)

    assignments = await get_assignment_map(client, code, alive, [name_to_token[n] for n in alive])
    victim = assignments[alive[0]]["target_name"]
    await confirm_death(client, code, name_to_token[victim])

    resp = await client.get(
        f"/api/games/{code}/leaderboard",
        headers={"X-Player-Token": tokens[0]},
    )
    leaderboard = resp.json()

    dead_entries = [e for e in leaderboard if not e["is_alive"]]
    assert len(dead_entries) == 1
    assert dead_entries[0]["name"] == victim


@pytest.mark.asyncio
async def test_leaderboard_secondary_sort_by_name(client: AsyncClient):
    """Players with equal kills are sorted by name ascending."""
    names = ["Charlie", "Alice", "Bob"]
    code, tokens = await setup_startable_game(client, player_names=names)
    await start_game(client, code, tokens[0])

    # Before any deaths, all kills are 0.
    resp = await client.get(
        f"/api/games/{code}/leaderboard",
        headers={"X-Player-Token": tokens[0]},
    )
    leaderboard = resp.json()

    # All have 0 kills, so sorted by name ascending.
    leaderboard_names = [entry["name"] for entry in leaderboard]
    assert leaderboard_names == ["Alice", "Bob", "Charlie"]


@pytest.mark.asyncio
async def test_leaderboard_after_full_game(client: AsyncClient):
    """Leaderboard reflects final kill counts after a full game."""
    names = ["Alice", "Bob", "Charlie"]
    code, tokens = await setup_startable_game(client, player_names=names)
    await start_game(client, code, tokens[0])

    name_to_token = dict(zip(names, tokens))
    alive = list(names)
    expected_kills: dict[str, int] = {n: 0 for n in names}

    # Play through to completion.
    while len(alive) > 1:
        assignments = await get_assignment_map(
            client, code, alive, [name_to_token[n] for n in alive]
        )
        killer = alive[0]
        victim = assignments[killer]["target_name"]
        await confirm_death(client, code, name_to_token[victim])
        expected_kills[killer] += 1
        alive.remove(victim)

    # Verify leaderboard matches.
    resp = await client.get(
        f"/api/games/{code}/leaderboard",
        headers={"X-Player-Token": tokens[0]},
    )
    leaderboard = resp.json()

    for entry in leaderboard:
        assert entry["kills"] == expected_kills[entry["name"]], (
            f"{entry['name']}: expected {expected_kills[entry['name']]} kills, got {entry['kills']}"
        )


@pytest.mark.asyncio
async def test_leaderboard_requires_auth(client: AsyncClient):
    """Leaderboard requires a valid player token."""
    names = ["Alice", "Bob", "Charlie"]
    code, tokens = await setup_startable_game(client, player_names=names)

    # No token.
    resp = await client.get(f"/api/games/{code}/leaderboard")
    assert resp.status_code == 422

    # Invalid token.
    resp = await client.get(
        f"/api/games/{code}/leaderboard",
        headers={"X-Player-Token": "invalid-token"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_leaderboard_wrong_game_returns_403(client: AsyncClient):
    """A player from another game cannot access the leaderboard."""
    code_a, tokens_a = await setup_startable_game(client, player_names=["Alice", "Bob", "Charlie"])

    _, token_b = await create_game_and_join(client, "Dave")

    resp = await client.get(
        f"/api/games/{code_a}/leaderboard",
        headers={"X-Player-Token": token_b},
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Edge cases -- death validation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dead_player_cannot_die_again(client: AsyncClient):
    """A player who is already dead cannot confirm death again (400)."""
    names = ["Alice", "Bob", "Charlie"]
    code, tokens = await setup_startable_game(client, player_names=names)
    await start_game(client, code, tokens[0])

    name_to_token = dict(zip(names, tokens))

    assignments = await get_assignment_map(client, code, names, [name_to_token[n] for n in names])
    victim = assignments["Alice"]["target_name"]
    victim_token = name_to_token[victim]

    # First death -- should succeed.
    await confirm_death(client, code, victim_token)

    # Second death -- should fail.
    resp = await client.post(
        f"/api/games/{code}/deaths",
        headers={"X-Player-Token": victim_token},
    )
    assert resp.status_code == 400
    assert "already dead" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_cannot_die_if_game_not_in_progress(client: AsyncClient):
    """Cannot confirm death if game is still in LOBBY (400)."""
    names = ["Alice", "Bob", "Charlie"]
    code, tokens = await setup_startable_game(client, player_names=names)

    # Game is still in lobby -- not started.
    resp = await client.post(
        f"/api/games/{code}/deaths",
        headers={"X-Player-Token": tokens[0]},
    )
    assert resp.status_code == 400
    assert "not in progress" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_cannot_die_after_game_finished(client: AsyncClient):
    """Cannot confirm death if game is FINISHED (400)."""
    names = ["Alice", "Bob", "Charlie"]
    code, tokens = await setup_startable_game(client, player_names=names)
    await start_game(client, code, tokens[0])

    name_to_token = dict(zip(names, tokens))
    alive = list(names)

    # Play through to completion.
    while len(alive) > 1:
        assignments = await get_assignment_map(
            client, code, alive, [name_to_token[n] for n in alive]
        )
        victim = assignments[alive[0]]["target_name"]
        await confirm_death(client, code, name_to_token[victim])
        alive.remove(victim)

    # Game is now finished. The winner tries to "die".
    winner_token = name_to_token[alive[0]]
    resp = await client.post(
        f"/api/games/{code}/deaths",
        headers={"X-Player-Token": winner_token},
    )
    assert resp.status_code == 400
    assert "not in progress" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_player_from_different_game_cannot_die(client: AsyncClient):
    """A player from game B cannot confirm death in game A (403)."""
    code_a, tokens_a = await setup_startable_game(client, player_names=["Alice", "Bob", "Charlie"])
    await start_game(client, code_a, tokens_a[0])

    _, token_b = await create_game_and_join(client, "Dave")

    resp = await client.post(
        f"/api/games/{code_a}/deaths",
        headers={"X-Player-Token": token_b},
    )
    assert resp.status_code == 403
    assert "not a player" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_death_requires_auth(client: AsyncClient):
    """Death endpoint requires a valid player token."""
    names = ["Alice", "Bob", "Charlie"]
    code, tokens = await setup_startable_game(client, player_names=names)
    await start_game(client, code, tokens[0])

    # No token.
    resp = await client.post(f"/api/games/{code}/deaths")
    assert resp.status_code == 422

    # Invalid token.
    resp = await client.post(
        f"/api/games/{code}/deaths",
        headers={"X-Player-Token": "bad-token"},
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Detailed inheritance verification
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_inheritance_detailed_deactivation(client: AsyncClient):
    """After a death, verify old assignments are deactivated and new one is active.

    Setup: 4 players in a chain. Kill one, verify:
    - Killer's OLD assignment (targeting victim) is deactivated
    - Victim's assignment is deactivated
    - Killer's NEW assignment targets the victim's old target
    """
    names = ["Alice", "Bob", "Charlie", "Dave"]
    code, tokens = await setup_startable_game(client, player_names=names)
    await start_game(client, code, tokens[0])

    name_to_token = dict(zip(names, tokens))
    assignments_before = await get_assignment_map(
        client, code, names, [name_to_token[n] for n in names]
    )

    # Identify roles based on the chain.
    # Alice -> (Alice's target) -> (target's target) -> ...
    killer_name = "Alice"
    victim_name = assignments_before["Alice"]["target_name"]
    victim_target_name = assignments_before[victim_name]["target_name"]

    # Kill the victim.
    await confirm_death(client, code, name_to_token[victim_name])

    # Killer's new assignment should target the victim's old target.
    killer_resp = await client.get(
        f"/api/games/{code}/assignment",
        headers={"X-Player-Token": name_to_token[killer_name]},
    )
    assert killer_resp.status_code == 200
    new_assignment = killer_resp.json()
    assert new_assignment["target_name"] == victim_target_name

    # Victim has no active assignment.
    victim_resp = await client.get(
        f"/api/games/{code}/assignment",
        headers={"X-Player-Token": name_to_token[victim_name]},
    )
    assert victim_resp.status_code == 404

    # Non-involved players' assignments are unchanged.
    alive_names = [n for n in names if n != victim_name]
    for name in alive_names:
        if name == killer_name:
            continue  # killer's assignment changed
        resp = await client.get(
            f"/api/games/{code}/assignment",
            headers={"X-Player-Token": name_to_token[name]},
        )
        assert resp.status_code == 200
        assert resp.json() == assignments_before[name], f"{name}'s assignment changed unexpectedly"


@pytest.mark.asyncio
async def test_sequential_kills_by_same_player(client: AsyncClient):
    """A player who kills multiple times accumulates kills correctly.

    With 5 players in a chain: A->B->C->D->E->A
    If B dies, A inherits B's target (C). Then if C dies, A inherits C's target (D).
    A should have 2 kills.
    """
    names = ["Alice", "Bob", "Charlie", "Dave", "Eve"]
    code, tokens = await setup_startable_game(client, player_names=names)
    await start_game(client, code, tokens[0])

    name_to_token = dict(zip(names, tokens))
    alive = list(names)

    # Kill 1: Alice's target dies.
    assignments = await get_assignment_map(client, code, alive, [name_to_token[n] for n in alive])
    victim1 = assignments["Alice"]["target_name"]
    result1 = await confirm_death(client, code, name_to_token[victim1])
    assert result1["killer_name"] == "Alice"
    assert result1["kill_count"] == 1
    alive.remove(victim1)

    # Kill 2: Alice's NEW target dies (inherited from victim1).
    assignments = await get_assignment_map(client, code, alive, [name_to_token[n] for n in alive])
    victim2 = assignments["Alice"]["target_name"]
    result2 = await confirm_death(client, code, name_to_token[victim2])
    assert result2["killer_name"] == "Alice"
    assert result2["kill_count"] == 2
    alive.remove(victim2)

    # Alice should have 2 kills in game state.
    game_resp = await client.get(f"/api/games/{code}")
    player_states = {p["name"]: p for p in game_resp.json()["players"]}
    assert player_states["Alice"]["kills"] == 2


@pytest.mark.asyncio
async def test_every_death_reduces_alive_count_by_one(client: AsyncClient):
    """After each death, the alive player count decreases by exactly 1."""
    names = ["Alice", "Bob", "Charlie", "Dave", "Eve"]
    code, tokens = await setup_startable_game(client, player_names=names)
    await start_game(client, code, tokens[0])

    name_to_token = dict(zip(names, tokens))
    alive = list(names)

    for death_num in range(4):
        expected_alive = len(names) - death_num

        game_resp = await client.get(f"/api/games/{code}")
        actual_alive = sum(1 for p in game_resp.json()["players"] if p["is_alive"])
        assert actual_alive == expected_alive, (
            f"After {death_num} deaths: expected {expected_alive} alive, got {actual_alive}"
        )

        assignments = await get_assignment_map(
            client, code, alive, [name_to_token[n] for n in alive]
        )
        victim = assignments[alive[0]]["target_name"]
        await confirm_death(client, code, name_to_token[victim])
        alive.remove(victim)

    # Final: 1 alive.
    game_resp = await client.get(f"/api/games/{code}")
    actual_alive = sum(1 for p in game_resp.json()["players"] if p["is_alive"])
    assert actual_alive == 1
