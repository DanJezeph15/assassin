"""Game code generation utilities.

Generates unique 6-character uppercase alphanumeric codes for games.
"""

import secrets
import string

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.game import Game

# Characters used in game codes: uppercase letters + digits, excluding
# ambiguous characters (0/O, 1/I/L) for readability.
_ALPHABET = "".join(
    c for c in string.ascii_uppercase + string.digits
    if c not in "OIL01"
)
_CODE_LENGTH = 6
_MAX_RETRIES = 10


async def generate_game_code(db: AsyncSession) -> str:
    """Generate a unique 6-character uppercase alphanumeric game code.

    Checks the database for collisions and retries up to _MAX_RETRIES times.
    In practice, with 36^6 (~2.2 billion) possible codes and a small number
    of active games, collisions are astronomically unlikely.

    Raises:
        RuntimeError: If a unique code could not be generated after max retries.
    """
    for _ in range(_MAX_RETRIES):
        code = "".join(secrets.choice(_ALPHABET) for _ in range(_CODE_LENGTH))

        result = await db.execute(
            select(Game.id).where(Game.code == code)
        )
        if result.scalar_one_or_none() is None:
            return code

    raise RuntimeError(
        f"Failed to generate a unique game code after {_MAX_RETRIES} attempts"
    )
