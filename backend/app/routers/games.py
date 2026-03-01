"""Games router -- create and retrieve games, start game, get assignment, death, leaderboard."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.dependencies import get_current_player, get_db
from app.models.assignment import Assignment
from app.models.game import GameStatus
from app.models.player import Player
from app.schemas.assignment import AssignmentResponse
from app.schemas.death import DeathResponse, LeaderboardEntry
from app.schemas.game import GameDetail, GameResponse
from app.services import assignment_service, death_service, game_service

router = APIRouter(prefix="/api/games", tags=["games"])


@router.post(
    "",
    response_model=GameResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new game",
)
async def create_game(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GameResponse:
    """Create a new game in LOBBY status with a unique 6-character join code."""
    game = await game_service.create_game(db)
    return GameResponse.model_validate(game)


@router.get(
    "/{code}",
    response_model=GameDetail,
    summary="Get game details",
)
async def get_game(
    code: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GameDetail:
    """Get full game state including players, rooms, and weapons.

    This is the main polling endpoint -- the frontend calls this to get
    current game state.
    """
    game = await game_service.get_game_by_code(db, code)
    return GameDetail.model_validate(game)


@router.post(
    "/{code}/start",
    summary="Start a game (host only)",
    status_code=status.HTTP_200_OK,
)
async def start_game(
    code: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_player: Annotated[Player, Depends(get_current_player)],
) -> dict[str, str]:
    """Start the game, generating the circular kill chain.

    Only the host can start the game. Requires:
    - Caller is the host
    - Game is in LOBBY status
    - At least 3 players
    - At least 1 room
    - At least 1 weapon
    """
    game = await game_service.validate_game_lobby(db, code, current_player)

    # Host-only check (not covered by validate_game_lobby).
    if current_player.id != game.host_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the host can start the game",
        )

    # Validate minimum requirements.
    if len(game.players) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 3 players are required to start the game",
        )

    if len(game.rooms) < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 1 room is required to start the game",
        )

    if len(game.weapons) < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 1 weapon is required to start the game",
        )

    # Generate the kill chain.
    await assignment_service.generate_kill_chain(db, game)

    # Transition to IN_PROGRESS.
    game.status = GameStatus.IN_PROGRESS
    await db.commit()

    return {"status": "in_progress"}


@router.get(
    "/{code}/assignment",
    response_model=AssignmentResponse,
    summary="Get your current assignment",
)
async def get_assignment(
    code: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_player: Annotated[Player, Depends(get_current_player)],
) -> AssignmentResponse:
    """Return the calling player's active assignment.

    Returns the target name, room name, and weapon name. Returns 404 if the
    player has no active assignment (game not started or player is dead).
    """
    await game_service.validate_game_membership(db, code, current_player)

    # Look up the player's active assignment with joined relationships.
    result = await db.execute(
        select(Assignment)
        .where(
            Assignment.killer_id == current_player.id,
            Assignment.is_active == True,  # noqa: E712
        )
        .options(
            selectinload(Assignment.target),
            selectinload(Assignment.room),
            selectinload(Assignment.weapon),
        )
    )
    assignment = result.scalar_one_or_none()

    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active assignment found",
        )

    return AssignmentResponse(
        target_name=assignment.target.name,
        room_name=assignment.room.name,
        weapon_name=assignment.weapon.name,
    )


@router.post(
    "/{code}/deaths",
    response_model=DeathResponse,
    summary="Confirm your own death",
    status_code=status.HTTP_200_OK,
)
async def confirm_death(
    code: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_player: Annotated[Player, Depends(get_current_player)],
) -> DeathResponse:
    """The calling player confirms they have been killed.

    Processes the death: marks them dead, increments the killer's kill count,
    deactivates both old assignments, creates a new assignment for the killer
    inheriting the victim's target/room/weapon, and checks for game over.
    """
    await game_service.validate_game_in_progress(db, code, current_player)

    # Player must be alive.
    if not current_player.is_alive:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already dead",
        )

    result = await death_service.process_death(db, current_player)
    await db.commit()

    return DeathResponse(
        killer_name=result["killer_name"],
        kill_count=result["kill_count"],
        game_over=result["game_over"],
        winner_name=result["winner_name"],
    )


@router.get(
    "/{code}/leaderboard",
    response_model=list[LeaderboardEntry],
    summary="Get the kill leaderboard",
)
async def get_leaderboard(
    code: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_player: Annotated[Player, Depends(get_current_player)],
) -> list[LeaderboardEntry]:
    """Return all players sorted by kills descending, then name ascending."""
    game = await game_service.validate_game_membership(db, code, current_player)

    # Query players sorted by kills desc, then name asc.
    result = await db.execute(
        select(Player)
        .where(Player.game_id == game.id)
        .order_by(Player.kills.desc(), Player.name.asc())
    )
    players = result.scalars().all()

    return [
        LeaderboardEntry(
            name=p.name,
            kills=p.kills,
            is_alive=p.is_alive,
        )
        for p in players
    ]
