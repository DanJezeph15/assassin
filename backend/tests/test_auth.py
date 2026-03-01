"""Tests for user authentication endpoints (Phase 6).

Covers registration, login, profile, game listing, session restore,
session linking, and join-with-auth integration.
"""

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def register_user(
    client: AsyncClient,
    username: str = "testuser",
    password: str = "password123",
) -> tuple[str, dict]:
    """Register a user and return (auth_token, user_data)."""
    resp = await client.post(
        "/api/auth/register",
        json={"username": username, "password": password},
    )
    data = resp.json()
    return data["token"], data["user"]


async def create_game_and_join(
    client: AsyncClient,
    player_name: str = "Alice",
    auth_token: str | None = None,
) -> tuple[str, str]:
    """Create a game, join as a player, return (code, player_token).

    If auth_token is provided, sends the Authorization header so the
    player record is linked to the user account.
    """
    create_resp = await client.post("/api/games")
    code = create_resp.json()["code"]

    headers: dict[str, str] = {}
    if auth_token is not None:
        headers["Authorization"] = f"Bearer {auth_token}"

    join_resp = await client.post(
        f"/api/games/{code}/players",
        json={"name": player_name},
        headers=headers,
    )
    player_token = join_resp.json()["token"]

    return code, player_token


# ---------------------------------------------------------------------------
# Registration tests -- POST /api/auth/register
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    """POST /api/auth/register returns 201 with token and correct username."""
    resp = await client.post(
        "/api/auth/register",
        json={"username": "Alice", "password": "secret123"},
    )

    assert resp.status_code == 201
    data = resp.json()
    assert "token" in data
    assert data["user"]["username"] == "Alice"
    assert "id" in data["user"]
    assert "created_at" in data["user"]


@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient):
    """Registering with an already-taken username returns 409."""
    await register_user(client, username="Alice")

    resp = await client.post(
        "/api/auth/register",
        json={"username": "Alice", "password": "password456"},
    )

    assert resp.status_code == 409
    assert "already taken" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_case_insensitive_duplicate(client: AsyncClient):
    """Registering 'alice' when 'Alice' exists returns 409."""
    await register_user(client, username="Alice")

    resp = await client.post(
        "/api/auth/register",
        json={"username": "alice", "password": "password456"},
    )

    assert resp.status_code == 409
    assert "already taken" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_short_username(client: AsyncClient):
    """Username shorter than 3 characters returns 422."""
    resp = await client.post(
        "/api/auth/register",
        json={"username": "ab", "password": "password123"},
    )

    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_register_short_password(client: AsyncClient):
    """Password shorter than 6 characters returns 422."""
    resp = await client.post(
        "/api/auth/register",
        json={"username": "validuser", "password": "12345"},
    )

    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_register_invalid_username_with_spaces(client: AsyncClient):
    """Username with spaces returns 422."""
    resp = await client.post(
        "/api/auth/register",
        json={"username": "user name", "password": "password123"},
    )

    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_register_invalid_username_with_special_chars(client: AsyncClient):
    """Username with special characters like @ returns 422."""
    resp = await client.post(
        "/api/auth/register",
        json={"username": "user@name", "password": "password123"},
    )

    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Login tests -- POST /api/auth/login
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """POST /api/auth/login returns 200 with token and user info."""
    await register_user(client, username="Alice", password="secret123")

    resp = await client.post(
        "/api/auth/login",
        json={"username": "Alice", "password": "secret123"},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    assert data["user"]["username"] == "Alice"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    """Login with a wrong password returns 401."""
    await register_user(client, username="Alice", password="secret123")

    resp = await client.post(
        "/api/auth/login",
        json={"username": "Alice", "password": "wrongpassword"},
    )

    assert resp.status_code == 401
    assert "invalid" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """Login with a username that does not exist returns 401."""
    resp = await client.post(
        "/api/auth/login",
        json={"username": "nobody", "password": "password123"},
    )

    assert resp.status_code == 401
    assert "invalid" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_case_insensitive_username(client: AsyncClient):
    """Register as 'Alice', login as 'alice' succeeds."""
    await register_user(client, username="Alice", password="secret123")

    resp = await client.post(
        "/api/auth/login",
        json={"username": "alice", "password": "secret123"},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["user"]["username"] == "Alice"  # original casing preserved


# ---------------------------------------------------------------------------
# Profile tests -- GET /api/auth/me
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_profile(client: AsyncClient):
    """GET /api/auth/me with a valid JWT returns user info."""
    auth_token, user_data = await register_user(client)

    resp = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == user_data["id"]
    assert data["username"] == user_data["username"]


@pytest.mark.asyncio
async def test_get_profile_missing_header(client: AsyncClient):
    """GET /api/auth/me without Authorization header returns 422."""
    resp = await client.get("/api/auth/me")

    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_profile_invalid_token(client: AsyncClient):
    """GET /api/auth/me with a bad JWT returns 401."""
    resp = await client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer totally-invalid-jwt-token"},
    )

    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Game listing tests -- GET /api/auth/me/games
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_games_empty_for_new_user(client: AsyncClient):
    """GET /api/auth/me/games returns paginated shape with empty items for a new user."""
    auth_token, _ = await register_user(client)

    resp = await client.get(
        "/api/auth/me/games",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["per_page"] == 25
    assert data["pages"] == 1


@pytest.mark.asyncio
async def test_games_shows_linked_game(client: AsyncClient):
    """After joining a game with auth, /me/games lists it."""
    auth_token, _ = await register_user(client)

    # Join a game with the auth token so the player is linked.
    code, _player_token = await create_game_and_join(
        client, player_name="TestPlayer", auth_token=auth_token
    )

    resp = await client.get(
        "/api/auth/me/games",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert resp.status_code == 200
    games = resp.json()["items"]
    assert len(games) == 1
    assert games[0]["game_code"] == code
    assert games[0]["player_name"] == "TestPlayer"


@pytest.mark.asyncio
async def test_games_pagination_defaults(client: AsyncClient):
    """Creating 3 games returns them in default page=1/per_page=25 shape."""
    auth_token, _ = await register_user(client)
    for i in range(3):
        await create_game_and_join(client, player_name=f"P{i}", auth_token=auth_token)

    resp = await client.get(
        "/api/auth/me/games",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    data = resp.json()
    assert data["total"] == 3
    assert data["page"] == 1
    assert data["per_page"] == 25
    assert data["pages"] == 1
    assert len(data["items"]) == 3


@pytest.mark.asyncio
async def test_games_pagination_second_page(client: AsyncClient):
    """Creating 30 games then requesting page 2 returns 5 items."""
    auth_token, _ = await register_user(client)
    for i in range(30):
        await create_game_and_join(client, player_name=f"P{i}", auth_token=auth_token)

    resp = await client.get(
        "/api/auth/me/games?page=2&per_page=25",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    data = resp.json()
    assert data["total"] == 30
    assert data["page"] == 2
    assert data["per_page"] == 25
    assert data["pages"] == 2
    assert len(data["items"]) == 5


@pytest.mark.asyncio
async def test_games_pagination_custom_per_page(client: AsyncClient):
    """Custom per_page=2 with 5 games gives 3 pages."""
    auth_token, _ = await register_user(client)
    for i in range(5):
        await create_game_and_join(client, player_name=f"P{i}", auth_token=auth_token)

    resp = await client.get(
        "/api/auth/me/games?per_page=2",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    data = resp.json()
    assert data["total"] == 5
    assert data["per_page"] == 2
    assert data["pages"] == 3
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_games_pagination_beyond_last_page(client: AsyncClient):
    """Requesting a page beyond the last returns empty items but correct total."""
    auth_token, _ = await register_user(client)
    for i in range(3):
        await create_game_and_join(client, player_name=f"P{i}", auth_token=auth_token)

    resp = await client.get(
        "/api/auth/me/games?page=99",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    data = resp.json()
    assert data["total"] == 3
    assert data["page"] == 99
    assert data["items"] == []


@pytest.mark.asyncio
async def test_games_ordered_by_created_at_desc(client: AsyncClient):
    """Games are returned with created_at in non-ascending order."""
    auth_token, _ = await register_user(client)
    for i in range(3):
        await create_game_and_join(client, player_name=f"P{i}", auth_token=auth_token)

    resp = await client.get(
        "/api/auth/me/games",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    items = resp.json()["items"]
    assert len(items) == 3
    # Verify created_at values are in non-ascending order
    timestamps = [item["created_at"] for item in items]
    for i in range(len(timestamps) - 1):
        assert timestamps[i] >= timestamps[i + 1]


@pytest.mark.asyncio
async def test_games_includes_created_at(client: AsyncClient):
    """Each game item includes a created_at field."""
    auth_token, _ = await register_user(client)
    await create_game_and_join(client, player_name="Alice", auth_token=auth_token)

    resp = await client.get(
        "/api/auth/me/games",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    items = resp.json()["items"]
    assert len(items) == 1
    assert "created_at" in items[0]
    assert items[0]["created_at"] is not None


# ---------------------------------------------------------------------------
# Session restore tests -- POST /api/auth/me/games/{code}/restore-session
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_restore_session_success(client: AsyncClient):
    """Restoring a session returns the player token for the linked game."""
    auth_token, _ = await register_user(client)
    code, player_token = await create_game_and_join(
        client, player_name="Alice", auth_token=auth_token
    )

    resp = await client.post(
        f"/api/auth/me/games/{code}/restore-session",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["token"] == player_token
    assert data["player_name"] == "Alice"
    assert "player_id" in data


@pytest.mark.asyncio
async def test_restore_session_not_found(client: AsyncClient):
    """Restoring a session for a game the user hasn't joined returns 404."""
    auth_token, _ = await register_user(client)

    # Create a game but DON'T join with auth -- join anonymously.
    create_resp = await client.post("/api/games")
    code = create_resp.json()["code"]
    await client.post(
        f"/api/games/{code}/players",
        json={"name": "Anonymous"},
    )

    resp = await client.post(
        f"/api/auth/me/games/{code}/restore-session",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert resp.status_code == 404
    assert "no player session" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Link sessions tests -- POST /api/auth/me/link-sessions
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_link_sessions_success(client: AsyncClient):
    """Linking an anonymous player token to an account succeeds."""
    auth_token, _ = await register_user(client)

    # Join a game anonymously (no auth header).
    code, player_token = await create_game_and_join(client, player_name="AnonPlayer")

    # Link the anonymous player to the user account.
    resp = await client.post(
        "/api/auth/me/link-sessions",
        json={"tokens": [player_token]},
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert resp.status_code == 200
    assert resp.json()["linked_count"] == 1

    # Verify the game now appears in /me/games.
    games_resp = await client.get(
        "/api/auth/me/games",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    games = games_resp.json()["items"]
    assert len(games) == 1
    assert games[0]["game_code"] == code
    assert games[0]["player_name"] == "AnonPlayer"


@pytest.mark.asyncio
async def test_link_sessions_no_overwrite(client: AsyncClient):
    """Linking does not overwrite a player already linked to a different user."""
    # Register two users.
    token_a, _ = await register_user(client, username="UserA", password="password123")
    token_b, _ = await register_user(client, username="UserB", password="password456")

    # User A joins a game with auth (player is linked to User A).
    code, player_token = await create_game_and_join(
        client, player_name="PlayerA", auth_token=token_a
    )

    # User B tries to link that same player token.
    resp = await client.post(
        "/api/auth/me/link-sessions",
        json={"tokens": [player_token]},
        headers={"Authorization": f"Bearer {token_b}"},
    )

    assert resp.status_code == 200
    assert resp.json()["linked_count"] == 0  # Should not have linked anything.

    # Verify the player is still linked to User A via session restore.
    restore_resp = await client.post(
        f"/api/auth/me/games/{code}/restore-session",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert restore_resp.status_code == 200
    assert restore_resp.json()["token"] == player_token

    # User B should NOT be able to restore that session.
    restore_resp_b = await client.post(
        f"/api/auth/me/games/{code}/restore-session",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert restore_resp_b.status_code == 404


# ---------------------------------------------------------------------------
# Join with auth integration tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_join_with_auth_sets_user_id(client: AsyncClient):
    """Joining a game with an Authorization header links the player to the user."""
    auth_token, user_data = await register_user(client)

    code, player_token = await create_game_and_join(
        client, player_name="AuthPlayer", auth_token=auth_token
    )

    # Confirm the link works by restoring the session.
    resp = await client.post(
        f"/api/auth/me/games/{code}/restore-session",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert resp.status_code == 200
    assert resp.json()["token"] == player_token
    assert resp.json()["player_name"] == "AuthPlayer"


@pytest.mark.asyncio
async def test_join_without_auth_no_user_id(client: AsyncClient):
    """Joining a game without auth does not link to any user account."""
    auth_token, _ = await register_user(client)

    # Join WITHOUT auth header.
    code, _player_token = await create_game_and_join(client, player_name="AnonPlayer")

    # The user should not be able to restore a session for this game.
    resp = await client.post(
        f"/api/auth/me/games/{code}/restore-session",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert resp.status_code == 404
