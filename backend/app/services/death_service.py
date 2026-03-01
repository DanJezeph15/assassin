"""Death service -- death processing and kill chain inheritance.

When a player dies:
1. Mark them as dead.
2. Find who was assigned to kill them (the killer).
3. Increment the killer's kill count.
4. Deactivate the killer's old assignment.
5. Find the victim's active assignment (who they were supposed to kill next).
6. Create a NEW assignment for the killer, inheriting the victim's target, room, and weapon.
7. Deactivate the victim's assignment.
8. Check if only 1 player remains alive -- if so, the game is over.
"""

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.assignment import Assignment
from app.models.game import Game, GameStatus
from app.models.player import Player


async def process_death(db: AsyncSession, victim: Player) -> dict:
    """Process a player's death, updating the kill chain accordingly.

    Args:
        db: The async database session. Uses flush() -- caller must commit.
        victim: The Player who has died.

    Returns:
        A dict with keys:
            - killer_name: Name of the player who killed the victim.
            - kill_count: The killer's updated kill count.
            - game_over: Whether the game has ended (1 alive player remaining).
            - winner_name: Name of the winner if game_over is True, else None.
    """
    # 1. Mark the victim as dead.
    victim.is_alive = False

    # 2. Find who was assigned to kill the victim (the killer's active assignment
    #    where target_id == victim.id).
    killer_assignment_result = await db.execute(
        select(Assignment)
        .where(
            Assignment.game_id == victim.game_id,
            Assignment.target_id == victim.id,
            Assignment.is_active == True,  # noqa: E712
        )
        .options(selectinload(Assignment.killer))
    )
    killer_assignment = killer_assignment_result.scalar_one_or_none()
    if killer_assignment is None:
        raise HTTPException(
            status_code=500,
            detail="Kill chain integrity error: no assignment targeting this player",
        )
    killer = killer_assignment.killer

    # 3. Increment the killer's kill count.
    killer.kills += 1

    # 4. Deactivate the killer's old assignment (the one targeting the victim).
    killer_assignment.is_active = False

    # 5. Find the victim's active assignment (who the victim was supposed to kill).
    victim_assignment_result = await db.execute(
        select(Assignment)
        .where(
            Assignment.game_id == victim.game_id,
            Assignment.killer_id == victim.id,
            Assignment.is_active == True,  # noqa: E712
        )
    )
    victim_assignment = victim_assignment_result.scalar_one_or_none()
    if victim_assignment is None:
        raise HTTPException(
            status_code=500,
            detail="Kill chain integrity error: no active assignment for this player",
        )

    # 6. Create a NEW assignment for the killer, inheriting the victim's
    #    target, room, and weapon.
    new_assignment = Assignment(
        game_id=victim.game_id,
        killer_id=killer.id,
        target_id=victim_assignment.target_id,
        room_id=victim_assignment.room_id,
        weapon_id=victim_assignment.weapon_id,
        is_active=True,
    )
    db.add(new_assignment)

    # 7. Deactivate the victim's assignment.
    victim_assignment.is_active = False

    # 8. Check for game over: count alive players in this game.
    alive_count_result = await db.execute(
        select(func.count())
        .select_from(Player)
        .where(
            Player.game_id == victim.game_id,
            Player.is_alive == True,  # noqa: E712
        )
    )
    alive_count = alive_count_result.scalar_one()

    game_over = alive_count == 1
    winner_name: str | None = None

    if game_over:
        # Set game status to FINISHED.
        game_result = await db.execute(
            select(Game).where(Game.id == victim.game_id)
        )
        game = game_result.scalar_one()
        game.status = GameStatus.FINISHED

        # The winner is the last alive player (the killer).
        winner_name = killer.name

        # Deactivate the killer's new assignment since the game is over.
        new_assignment.is_active = False

    await db.flush()

    return {
        "killer_name": killer.name,
        "kill_count": killer.kills,
        "game_over": game_over,
        "winner_name": winner_name,
    }
