"""Game service -- business logic for game creation, lookup, and player joining."""

import secrets

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.game import Game, GameStatus
from app.models.player import Player
from app.utils.codes import generate_game_code


async def create_game(db: AsyncSession) -> Game:
    """Create a new game in LOBBY status with a unique join code."""
    code = await generate_game_code(db)

    game = Game(code=code, status=GameStatus.LOBBY)
    db.add(game)
    await db.commit()
    await db.refresh(game)

    return game


async def get_game_by_code(db: AsyncSession, code: str) -> Game:
    """Fetch a game by its join code with all relationships eagerly loaded.

    Raises:
        HTTPException(404): If no game with the given code exists.
    """
    result = await db.execute(
        select(Game)
        .where(Game.code == code.upper())
        .options(
            selectinload(Game.players),
            selectinload(Game.rooms),
            selectinload(Game.weapons),
        )
    )
    game = result.scalar_one_or_none()

    if game is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game with code '{code.upper()}' not found",
        )

    return game


async def validate_game_lobby(db: AsyncSession, code: str, player: Player) -> Game:
    """Fetch game by code, verify it's in LOBBY status, and verify the player belongs to it.

    Returns the game. Raises HTTPException on failure.
    """
    game = await get_game_by_code(db, code)
    if game.status != GameStatus.LOBBY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Game is not in the lobby",
        )
    if player.game_id != game.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a player in this game",
        )
    return game


async def validate_game_membership(db: AsyncSession, code: str, player: Player) -> Game:
    """Fetch game and verify player belongs to it."""
    game = await get_game_by_code(db, code)
    if player.game_id != game.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a player in this game",
        )
    return game


async def validate_game_in_progress(db: AsyncSession, code: str, player: Player) -> Game:
    """Fetch game, verify membership, and verify game is in progress."""
    game = await validate_game_membership(db, code, player)
    if game.status != GameStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Game is not in progress",
        )
    return game


async def join_game(db: AsyncSession, code: str, player_name: str) -> Player:
    """Add a player to a game.

    Validates:
    - Game exists
    - Game is in LOBBY status (cannot join an in-progress or finished game)
    - Player name is not already taken in this game

    The first player to join becomes the game host.

    Returns:
        The newly created Player with their auth token.

    Raises:
        HTTPException(404): Game not found.
        HTTPException(400): Game not in lobby or name already taken.
    """
    game = await get_game_by_code(db, code)

    if game.status != GameStatus.LOBBY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot join a game that is not in the lobby",
        )

    # Check for duplicate name (case-insensitive).
    for existing_player in game.players:
        if existing_player.name.lower() == player_name.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Name '{player_name}' is already taken in this game",
            )

    token = secrets.token_hex(32)  # 64-char hex string

    player = Player(
        game_id=game.id,
        name=player_name,
        token=token,
    )
    db.add(player)

    # The first player to join becomes the host.
    # We must flush first so the player gets an id assigned.
    is_first_player = len(game.players) == 0
    await db.flush()

    if is_first_player:
        game.host_id = player.id

    await db.commit()
    await db.refresh(player)

    return player
