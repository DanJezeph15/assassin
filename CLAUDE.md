# Airbnb Games

A website for playing party games with friends during Airbnb stays.

## Tech Stack

### Backend
- **Framework:** FastAPI (Python 3.12)
- **Database:** SQLite (async via aiosqlite + SQLAlchemy 2.x)
- **Migrations:** Alembic
- **Config:** pydantic-settings + python-dotenv
- **Server:** Uvicorn (port 8000)

### Frontend
- **Framework:** React 19 + TypeScript
- **Routing:** React Router v7
- **Styling:** Tailwind CSS 3
- **Build Tool:** Vite 7

### Project Structure
```
backend/
  app/
    models/       # SQLAlchemy models (game, player, assignment, room, weapon)
    routers/      # API endpoints (games, players, rooms, weapons)
    schemas/      # Pydantic request/response schemas
    services/     # Business logic (assignment, death, game services)
    utils/        # Helpers (join code generation)
    database.py   # Async engine & session setup
    config.py     # Settings via pydantic-settings
    main.py       # FastAPI app entry point
  alembic/        # DB migrations
frontend/
  src/
    pages/        # HomePage, LobbyPage, GamePage, DeadPage, GameOverPage
    components/   # UI components (PlayerList, Leaderboard, AssignmentCard, etc.)
    api/          # API client & endpoint wrappers
    hooks/        # Custom hooks (usePolling)
    types/        # TypeScript type definitions
    utils/        # Helpers (local storage)
```

## Games

### Assassin

A real-life Cluedo-style elimination game. Each player is secretly assigned a target to "kill" using a specific weapon in a specific room of the Airbnb.

#### Game Setup

1. **Create a game** — One person creates a new Assassin game and gets a lobby/join code.
2. **Players join** — Everyone joins the game and enters their name. The player list is built from whoever joins.
3. **Add rooms and weapons** — Any player can add rooms (e.g. "Kitchen", "Master Bedroom") and murder weapons (e.g. "Mug", "Spatula", "TV Remote") to the shared pool.
4. **Start the game** — When everyone is ready, the host clicks "Start Game".

#### Game Start — Assignment Shuffle

On start, the game:

- Shuffles all players into a secret kill chain (A → B → C → ... → A), so every player has exactly one target and is targeted by exactly one other player.
- Randomly assigns each player a **weapon** and a **room** from the shared pools.
- Each player receives a private prompt: **"Kill [Target] in the [Room] with the [Weapon]"**.

#### During the Game

- **View your assignment** — Each player can view their own prompt at any time. Only they can see it.
- **Making a kill** — In real life, you "kill" your target by getting them alone in the assigned room with the assigned weapon. Creativity and stealth encouraged.
- **Confirming a death** — When someone is killed, the victim confirms it by pressing an "I've been killed" button.

#### When a Player Dies

1. The victim is **removed from the game** (they're out).
2. The killer gets a **kill added to their score** (for the leaderboard).
3. The killer **inherits the victim's assignment**. Their prompt updates to the victim's target, room, and weapon.
   - Example: Dan has "Kill Maia in the Kitchen with a Mug". Maia has "Kill James in the Lounge with a Pan". Dan kills Maia → Maia is out, Dan now has "Kill James in the Lounge with a Pan".
4. This continues until only one player remains — the winner.

#### Leaderboard

Track kills per player across the game. Displayed during and after the game.

#### Key Rules

- The kill chain is circular so there is always exactly one winner (last person standing).
- Assignments are strictly private — no player should be able to see another's prompt.
- Only the victim can confirm their own death.
