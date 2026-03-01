"""Assignment service -- kill chain generation and assignment lookup."""

import random

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import Assignment
from app.models.game import Game


async def generate_kill_chain(db: AsyncSession, game: Game) -> list[Assignment]:
    """Generate a circular kill chain for all players in a game.

    Shuffles players into a random order and creates a ring:
        player[0] -> player[1] -> player[2] -> ... -> player[N-1] -> player[0]

    Each assignment gets a randomly chosen room and weapon from the game's pools.

    Args:
        db: The async database session.
        game: A Game with players, rooms, and weapons already loaded.

    Returns:
        The list of created Assignment records.
    """
    players = list(game.players)
    rooms = list(game.rooms)
    weapons = list(game.weapons)

    random.shuffle(players)

    assignments: list[Assignment] = []
    for i, killer in enumerate(players):
        target = players[(i + 1) % len(players)]
        room = random.choice(rooms)
        weapon = random.choice(weapons)

        assignment = Assignment(
            game_id=game.id,
            killer_id=killer.id,
            target_id=target.id,
            room_id=room.id,
            weapon_id=weapon.id,
            is_active=True,
        )
        db.add(assignment)
        assignments.append(assignment)

    await db.flush()
    return assignments
