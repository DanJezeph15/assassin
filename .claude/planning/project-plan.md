# Airbnb Games -- Implementation Plan

## Table of Contents

1. [Architectural Decisions & Tech Stack](#1-architectural-decisions--tech-stack)
2. [Project Structure](#2-project-structure)
3. [Data Models](#3-data-models)
4. [API Design](#4-api-design)
5. [Frontend Pages & Components](#5-frontend-pages--components)
6. [Implementation Phases](#6-implementation-phases)
7. [Testing Strategy](#7-testing-strategy)

---

## 1. Architectural Decisions & Tech Stack

### Context

This is a **party game** played in-person at an Airbnb. Players access it on their phones via a browser. Key characteristics:

- **State changes are infrequent**: Someone joins the lobby, adds a room, someone dies. These happen minutes apart, not milliseconds.
- **No user accounts**: Players are ephemeral -- join by name and code. No registration.
- **Mobile-first**: Players on phones walking around a house. UI must be touch-friendly.
- **Small scale**: 4-20 friends, not thousands of users. Simplicity over scalability.

### Backend: FastAPI (REST only)

**Framework**: FastAPI

**Why it fits**:
- Auto-generated OpenAPI docs for fast development and debugging.
- Pydantic v2 for request/response validation with zero boilerplate.
- Simple REST endpoints are all we need -- game events happen infrequently and players can refresh/poll to see updates.

**No WebSockets**: The game is played in real life. State changes (someone joins, someone dies) happen minutes apart. A simple page refresh or lightweight poll (every few seconds in the lobby) is more than sufficient and dramatically simpler to build and maintain.

### Database: SQLite

**Rationale**:
- The data model is tiny (games, players, rooms, weapons -- small tables with low row counts).
- No concurrent write pressure -- game state changes are sequential.
- Zero infrastructure -- no separate database server, no Docker, no connection pooling.
- SQLAlchemy 2.0+ supports async SQLite via aiosqlite. If we ever need PostgreSQL, we just change the connection string.

### ORM: SQLAlchemy 2.0 (async)

- Async sessions via `aiosqlite` driver.
- Alembic for migrations.

### Frontend: React + Vite + TypeScript + Tailwind CSS

**Why React + Vite**:
- Clear interactive states (lobby, game view, death confirmation, leaderboard) suit React's component model.
- Vite for instant HMR and fast builds.
- No Next.js -- this is a private SPA, no SEO needed.
- TypeScript for type safety.

**Styling**: Tailwind CSS -- utility-first, mobile-first responsive classes, no runtime overhead.

**State Management**: React Context + `useReducer`. The state tree is small (one game, its players, your assignment).

**Data Fetching**: Simple fetch calls to REST API. The lobby page polls every few seconds to pick up new players/rooms/weapons. The game page polls less frequently (or players just refresh).

### Architecture

```
Browser (React) --REST--> FastAPI Server <--> SQLite

Flow:
  1. Player loads page -> GET game state
  2. Player takes action -> POST/DELETE -> server updates DB -> returns new state
  3. Lobby auto-polls every ~5s to pick up changes from other players
  4. Game page: player refreshes or polls to see updates
```

### Deployment (Stretch / Out of Scope for MVP)

Single process (Uvicorn) behind Caddy or nginx on a cheap VPS. SQLite file on disk. No containers needed.

---

## 2. Project Structure

```
games/
├── CLAUDE.md
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI app, lifespan, CORS, router includes
│   │   ├── config.py                # Settings via Pydantic BaseSettings
│   │   ├── database.py              # SQLAlchemy engine, session factory, Base
│   │   ├── dependencies.py          # get_db, get_current_player
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── game.py              # Game model
│   │   │   ├── player.py            # Player model
│   │   │   ├── room.py              # Room model
│   │   │   ├── weapon.py            # Weapon model
│   │   │   └── assignment.py        # Assignment model (target, room, weapon per player)
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── game.py              # Game request/response schemas
│   │   │   ├── player.py            # Player schemas
│   │   │   ├── room.py              # Room schemas
│   │   │   ├── weapon.py            # Weapon schemas
│   │   │   └── assignment.py        # Assignment schemas
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── games.py             # Game CRUD + start game endpoint
│   │   │   ├── players.py           # Join/leave game
│   │   │   ├── rooms.py             # Add/remove rooms
│   │   │   └── weapons.py           # Add/remove weapons
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── game_service.py      # Game lifecycle logic
│   │   │   ├── assignment_service.py # Kill chain generation, assignment shuffling
│   │   │   └── death_service.py     # Death processing, chain inheritance
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── codes.py             # Game code generation (6-char alphanumeric)
│   ├── alembic/
│   │   ├── alembic.ini
│   │   ├── env.py
│   │   └── versions/
│   ├── tests/
│   │   ├── conftest.py              # Fixtures: test DB, async client, test game factory
│   │   ├── test_games.py
│   │   ├── test_players.py
│   │   ├── test_rooms_weapons.py
│   │   ├── test_assignments.py      # Kill chain logic tests
│   │   └── test_death.py            # Death processing tests
│   ├── requirements.txt
│   └── pyproject.toml
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── public/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── routes.tsx               # React Router route definitions
│   │   ├── api/
│   │   │   ├── client.ts            # Fetch wrapper with base URL and token header
│   │   │   └── endpoints.ts         # Typed API call functions
│   │   ├── hooks/
│   │   │   ├── usePolling.ts        # Generic polling hook (fetch on interval)
│   │   │   └── useGameState.ts      # Game state context consumer hook
│   │   ├── context/
│   │   │   └── GameContext.tsx       # Game state provider (useReducer-based)
│   │   ├── pages/
│   │   │   ├── HomePage.tsx          # Landing: create or join game
│   │   │   ├── LobbyPage.tsx         # Lobby: player list, rooms, weapons, start button
│   │   │   ├── GamePage.tsx          # Active game: your assignment, "I've been killed" button
│   │   │   ├── DeadPage.tsx          # Post-death: you're out, watch leaderboard
│   │   │   └── GameOverPage.tsx      # Game over: winner announcement, final leaderboard
│   │   ├── components/
│   │   │   ├── ui/                   # Reusable primitives (Button, Input, Card, Modal, Badge)
│   │   │   ├── PlayerList.tsx
│   │   │   ├── RoomList.tsx
│   │   │   ├── WeaponList.tsx
│   │   │   ├── AssignmentCard.tsx    # "Kill X in the Y with a Z"
│   │   │   ├── Leaderboard.tsx
│   │   │   ├── DeathConfirmModal.tsx # "Are you sure you've been killed?"
│   │   │   └── JoinForm.tsx
│   │   ├── types/
│   │   │   └── game.ts              # TypeScript types mirroring backend schemas
│   │   └── utils/
│   │       └── storage.ts           # localStorage helpers for player token
│   └── tests/                       # Vitest + React Testing Library
│       ├── setup.ts
│       └── components/
└── .claude/
    └── planning/
        └── project-plan.md
```

---

## 3. Data Models

### Entity-Relationship Overview

```
Game (1) ----< (N) Player
Game (1) ----< (N) Room
Game (1) ----< (N) Weapon
Player (1) ---< (0..1) Assignment  (active assignment; a player has at most one)
Assignment references: killer (Player), target (Player), Room, Weapon
```

### SQLAlchemy Models

#### Game
| Column       | Type         | Notes                                              |
|-------------|-------------|-----------------------------------------------------|
| id          | UUID (PK)    | Primary key                                         |
| code        | String(6)    | Unique join code, uppercase alphanumeric            |
| status      | Enum         | `lobby`, `in_progress`, `finished`                  |
| host_id     | UUID (FK)    | References Player.id (nullable until first player)  |
| created_at  | DateTime     | Auto-set                                            |
| updated_at  | DateTime     | Auto-updated                                        |

#### Player
| Column       | Type         | Notes                                              |
|-------------|-------------|-----------------------------------------------------|
| id          | UUID (PK)    | Primary key                                         |
| game_id     | UUID (FK)    | References Game.id                                  |
| name        | String(50)   | Display name                                        |
| is_alive    | Boolean      | True until killed                                   |
| kills       | Integer      | Kill count, starts at 0                             |
| token       | String(64)   | Secret player token for auth (set on join)          |
| joined_at   | DateTime     | Auto-set                                            |

**Auth note**: No user accounts. Each player gets a random token on join, stored in localStorage, sent via header with every request.

#### Room
| Column       | Type         | Notes                                              |
|-------------|-------------|-----------------------------------------------------|
| id          | UUID (PK)    | Primary key                                         |
| game_id     | UUID (FK)    | References Game.id                                  |
| name        | String(100)  | Room name ("Kitchen", "Master Bedroom")             |

#### Weapon
| Column       | Type         | Notes                                              |
|-------------|-------------|-----------------------------------------------------|
| id          | UUID (PK)    | Primary key                                         |
| game_id     | UUID (FK)    | References Game.id                                  |
| name        | String(100)  | Weapon name ("Mug", "Spatula")                      |

#### Assignment
| Column       | Type         | Notes                                              |
|-------------|-------------|-----------------------------------------------------|
| id          | UUID (PK)    | Primary key                                         |
| game_id     | UUID (FK)    | References Game.id                                  |
| killer_id   | UUID (FK)    | References Player.id -- the player who has this     |
| target_id   | UUID (FK)    | References Player.id -- the player to be killed     |
| room_id     | UUID (FK)    | References Room.id                                  |
| weapon_id   | UUID (FK)    | References Weapon.id                                |
| is_active   | Boolean      | True = current assignment; False = completed        |
| created_at  | DateTime     | When this assignment was created/inherited          |

### Key Indexes

- `Game.code` -- unique index (lookup by join code)
- `Player.game_id` -- index (list players in a game)
- `Player.token` -- unique index (auth lookup)
- `Assignment.killer_id + is_active` -- composite index (find player's current assignment)
- `Assignment.game_id + is_active` -- composite index (find all active assignments)

---

## 4. API Design

### REST Endpoints

All endpoints prefixed with `/api`. Player auth via `X-Player-Token` header.

#### Games

| Method | Path                    | Description                        | Auth     |
|--------|------------------------|------------------------------------|----------|
| POST   | `/api/games`           | Create a new game                  | None     |
| GET    | `/api/games/{code}`    | Get game details (players, rooms, weapons, status) | None     |

**POST /api/games**
- Request: `{}` (empty)
- Response: `{ game_id, code, status: "lobby" }`

**GET /api/games/{code}**
- Response: `{ game_id, code, status, host_id, players: [...], rooms: [...], weapons: [...] }`
- This is the main polling endpoint. The frontend calls this to get current game state.

#### Players

| Method | Path                           | Description                     | Auth         |
|--------|--------------------------------|---------------------------------|--------------|
| POST   | `/api/games/{code}/players`    | Join a game                     | None         |
| DELETE  | `/api/games/{code}/players/me` | Leave a game                    | Player token |

**POST /api/games/{code}/players**
- Request: `{ name: "Dan" }`
- Response: `{ player_id, name, token }` (token stored client-side)

#### Rooms

| Method | Path                           | Description                     | Auth         |
|--------|--------------------------------|---------------------------------|--------------|
| POST   | `/api/games/{code}/rooms`      | Add a room                      | Player token |
| DELETE  | `/api/games/{code}/rooms/{id}` | Remove a room                   | Player token |

#### Weapons

| Method | Path                             | Description                     | Auth         |
|--------|----------------------------------|---------------------------------|--------------|
| POST   | `/api/games/{code}/weapons`      | Add a weapon                    | Player token |
| DELETE  | `/api/games/{code}/weapons/{id}` | Remove a weapon                 | Player token |

#### Game Actions

| Method | Path                            | Description                     | Auth         |
|--------|----------------------------------|---------------------------------|--------------|
| POST   | `/api/games/{code}/start`       | Start the game (host only)      | Player token |
| POST   | `/api/games/{code}/deaths`      | Confirm your own death          | Player token |
| GET    | `/api/games/{code}/assignment`  | Get your current assignment     | Player token |
| GET    | `/api/games/{code}/leaderboard` | Get kill leaderboard            | Player token |

**POST /api/games/{code}/start**
- Validates: caller is host, game in lobby, >= 3 players, >= 1 room, >= 1 weapon.
- Generates kill chain, creates assignments, sets status to `in_progress`.

**POST /api/games/{code}/deaths**
- Request: `{}` (the authenticated player confirms their own death)
- Marks player as dead, increments killer's kills, creates new assignment for killer inheriting victim's target/room/weapon, checks for game over.

**GET /api/games/{code}/assignment**
- Returns calling player's active assignment: `{ target_name, room_name, weapon_name }`
- Returns null/empty if player is dead or game not started.

**GET /api/games/{code}/leaderboard**
- Returns all players sorted by kills descending: `[{ name, kills, is_alive }]`

---

## 5. Frontend Pages & Components

### Page Flow

```
HomePage ──> LobbyPage ──> GamePage ──> DeadPage
                                │           │
                                └───────────> GameOverPage
```

### Pages

#### HomePage (`/`)
- "Create Game" button and "Join Game" form (code + name inputs).
- On create: POST /api/games -> redirect to lobby.
- On join: POST /api/games/{code}/players -> store token in localStorage -> redirect to lobby.

#### LobbyPage (`/game/{code}`)
- Shows game code (large, copyable), player list, room list, weapon list.
- Any player can add rooms/weapons.
- Host sees "Start Game" button (disabled until >= 3 players, >= 1 room, >= 1 weapon).
- Polls `GET /api/games/{code}` every ~5 seconds to pick up changes.
- When game status changes to `in_progress`, redirects to GamePage.

#### GamePage (`/game/{code}/play`)
- Shows assignment card: "Kill [Target] in the [Room] with the [Weapon]".
- "I've Been Killed" button (red, requires confirmation modal).
- Mini leaderboard and alive/dead player list.
- Polls assignment + game state periodically to detect if target changed (someone else died) or game ended.

#### DeadPage (`/game/{code}/dead`)
- "You have been eliminated!" message.
- Live leaderboard and alive player count (polls periodically).
- Spectator mode.

#### GameOverPage (`/game/{code}/over`)
- Winner announcement.
- Final leaderboard with kill counts.
- "Play Again" button.

### Key Components

| Component            | Description                                                     |
|---------------------|-----------------------------------------------------------------|
| `Button`            | Reusable button with variants: primary, secondary, danger       |
| `Input`             | Styled text input with label and validation                     |
| `Card`              | Container with rounded corners, shadow, padding                 |
| `Modal`             | Centered overlay with backdrop                                  |
| `Badge`             | Small colored pill (player status: alive/dead/host)             |
| `PlayerList`        | List of players with status badges and kill counts              |
| `RoomList`          | Editable list of rooms with add/remove                          |
| `WeaponList`        | Editable list of weapons with add/remove                        |
| `AssignmentCard`    | The "Kill X in Y with Z" card, styled prominently               |
| `Leaderboard`       | Ranked list of players by kill count                            |
| `DeathConfirmModal` | "Are you sure?" confirmation before reporting death             |
| `JoinForm`          | Game code + name input form                                     |
| `GameCodeDisplay`   | Large, copyable game code                                       |

---

## 6. Implementation Phases

### Phase 0: Project Scaffolding
**Goal**: Both backend and frontend run with hot reload.

| # | Task | Size |
|---|------|------|
| 0.1 | Create `backend/` directory structure with empty `__init__.py` files | S |
| 0.2 | Write `pyproject.toml` and `requirements.txt` with dependencies | S |
| 0.3 | Write `backend/app/config.py` with Pydantic BaseSettings | S |
| 0.4 | Write `backend/app/database.py` with async SQLAlchemy engine + session factory | S |
| 0.5 | Write `backend/app/main.py` with FastAPI app, CORS, lifespan, health endpoint | S |
| 0.6 | Initialize Alembic with async SQLite config | S |
| 0.7 | Scaffold frontend with Vite + React + TypeScript | S |
| 0.8 | Install and configure Tailwind CSS | S |
| 0.9 | Install React Router, set up basic route structure with placeholder pages | S |
| 0.10 | Configure Vite proxy to forward `/api` to FastAPI on port 8000 | S |
| 0.11 | Verify both servers run and proxy works | S |

**Deliverable**: Running backend (8000) and frontend (5173) with hot reload and API proxy.

---

### Phase 1: Data Models & Database
**Goal**: All SQLAlchemy models defined, initial migration generated.

| # | Task | Size |
|---|------|------|
| 1.1 | Write Game model | S |
| 1.2 | Write Player model | S |
| 1.3 | Write Room model | S |
| 1.4 | Write Weapon model | S |
| 1.5 | Write Assignment model | S |
| 1.6 | Export all models from `__init__.py` | S |
| 1.7 | Generate initial Alembic migration | S |
| 1.8 | Run migration and verify tables | S |
| 1.9 | Basic model tests | M |

**Deliverable**: Complete database schema with migration.

---

### Phase 2: Game Creation & Player Joining
**Goal**: REST endpoints for creating games and joining via code.

| # | Task | Size |
|---|------|------|
| 2.1 | Write `utils/codes.py` -- 6-char code generator with uniqueness check | S |
| 2.2 | Write game schemas (GameCreate, GameResponse, GameDetail) | S |
| 2.3 | Write player schemas (PlayerJoin, PlayerResponse, PlayerWithToken) | S |
| 2.4 | Write `game_service.py` -- create_game(), get_game_by_code() | M |
| 2.5 | Write `routers/games.py` -- POST /api/games, GET /api/games/{code} | S |
| 2.6 | Write `dependencies.py` -- get_db session dep, get_current_player token auth dep | M |
| 2.7 | Write join logic: validate code, lobby status, name not taken, generate token | M |
| 2.8 | Write `routers/players.py` -- POST /api/games/{code}/players | S |
| 2.9 | Tests: create game, join game, duplicate name rejected, join after start rejected | M |

**Deliverable**: Can create and join games. Token-based identity works.

---

### Phase 3: Rooms & Weapons
**Goal**: CRUD for rooms and weapons in the lobby.

| # | Task | Size |
|---|------|------|
| 3.1 | Write room/weapon schemas | S |
| 3.2 | Write `routers/rooms.py` -- POST and DELETE | S |
| 3.3 | Write `routers/weapons.py` -- POST and DELETE | S |
| 3.4 | Validation: only allow changes when game is in lobby | S |
| 3.5 | Validation: prevent duplicate names within a game | S |
| 3.6 | Tests: add/remove rooms and weapons, validation edge cases | M |

**Deliverable**: Full CRUD for rooms and weapons.

---

### Phase 4: Game Start & Kill Chain
**Goal**: Host starts the game, circular kill chain is generated.

| # | Task | Size |
|---|------|------|
| 4.1 | Write `assignment_service.py` -- generate_kill_chain(players, rooms, weapons) | M |
| 4.2 | Implement circular shuffle: random player order into a ring (A->B->C->...->A) | M |
| 4.3 | Random room/weapon assignment for each player | S |
| 4.4 | Create Assignment records in DB | S |
| 4.5 | Write POST /api/games/{code}/start -- validate host, counts, call assignment service | M |
| 4.6 | Write GET /api/games/{code}/assignment -- return calling player's active assignment | S |
| 4.7 | Write assignment schemas | S |
| 4.8 | Thorough kill chain tests: circularity, uniqueness, valid rooms/weapons | L |
| 4.9 | Test start endpoint: validation, assignment creation | M |

**Deliverable**: Game starts. Each player gets a secret assignment. Chain is provably circular.

---

### Phase 5: Death & Assignment Inheritance
**Goal**: Death processing and kill chain updates. This is the hardest phase.

| # | Task | Size |
|---|------|------|
| 5.1 | Write `death_service.py` -- process_death(victim_player) | L |
| 5.2 | Death logic: mark dead, find killer, increment kills, deactivate both assignments, create new assignment for killer with victim's target/room/weapon | L |
| 5.3 | Game-over detection: if 1 alive player remains, set status to `finished` | S |
| 5.4 | Write POST /api/games/{code}/deaths | M |
| 5.5 | Write GET /api/games/{code}/leaderboard | S |
| 5.6 | Extensive tests: single death, sequential deaths through full game, winner detection | L |
| 5.7 | Edge cases: dead player can't die again, death only when in_progress | S |

**Deliverable**: Complete death processing with chain inheritance. Game ends correctly.

---

### Phase 6: Frontend -- Home Page & Join Flow
**Goal**: Players can create or join a game from their phone.

| # | Task | Size |
|---|------|------|
| 6.1 | Build UI primitives: Button, Input, Card components | M |
| 6.2 | Build HomePage layout: title, create button, join form | M |
| 6.3 | Write `api/client.ts` -- fetch wrapper with base URL and token header | S |
| 6.4 | Write `api/endpoints.ts` -- typed API functions | S |
| 6.5 | Implement create game flow: POST -> store code -> redirect to lobby | S |
| 6.6 | Implement join game flow: POST -> store token in localStorage -> redirect to lobby | S |
| 6.7 | Error handling: invalid code, name taken, game already started | S |
| 6.8 | Mobile-first styling: full-width inputs, large touch targets | S |

**Deliverable**: Players can create and join games.

---

### Phase 7: Frontend -- Lobby Page
**Goal**: Lobby with player list, rooms/weapons management, start button.

| # | Task | Size |
|---|------|------|
| 7.1 | Write `usePolling.ts` hook -- fetch on interval, returns data + loading state | S |
| 7.2 | Write `GameContext.tsx` -- state provider with game data from polling | M |
| 7.3 | Build PlayerList component | S |
| 7.4 | Build RoomList component with add/remove | M |
| 7.5 | Build WeaponList component with add/remove | M |
| 7.6 | Build GameCodeDisplay with copy-to-clipboard | S |
| 7.7 | Build LobbyPage: compose components, start button (host only, disabled until ready) | L |
| 7.8 | Wire up API calls for add/remove rooms and weapons | S |
| 7.9 | Auto-redirect to GamePage when polling detects game started | S |

**Deliverable**: Fully functional lobby. Polls for updates. Host can start.

---

### Phase 8: Frontend -- Game Page
**Goal**: Players see their assignment and can confirm death.

| # | Task | Size |
|---|------|------|
| 8.1 | Build AssignmentCard component | M |
| 8.2 | Build DeathConfirmModal | M |
| 8.3 | Build Leaderboard component | S |
| 8.4 | Build GamePage: assignment card, death button, player list, leaderboard | M |
| 8.5 | Wire up death confirmation: POST deaths -> redirect to dead page | S |
| 8.6 | Poll assignment endpoint to detect changes (new target after a kill) | S |
| 8.7 | Poll game state to detect game over -> redirect to game over page | S |
| 8.8 | Test with multiple browser tabs | M |

**Deliverable**: Players see assignments, confirm deaths, game progresses.

---

### Phase 9: Frontend -- Dead & Game Over Pages
**Goal**: Complete game lifecycle in the UI.

| # | Task | Size |
|---|------|------|
| 9.1 | Build DeadPage: eliminated message, live leaderboard, alive count | M |
| 9.2 | Build GameOverPage: winner announcement, final leaderboard | M |
| 9.3 | Handle browser refresh: restore correct page based on game status + alive status | M |
| 9.4 | End-to-end test: full game lifecycle across multiple tabs | L |

**Deliverable**: Complete game lifecycle from creation to winner.

---

### Phase 10: Polish & Hardening
**Goal**: Handle edge cases, make it feel good.

| # | Task | Size |
|---|------|------|
| 10.1 | Handle stale game state: game finished or doesn't exist | S |
| 10.2 | Loading states and empty states | S |
| 10.3 | Frontend input validation: name length, room/weapon name limits | S |
| 10.4 | Prevent double-submissions: disable buttons during API calls | S |
| 10.5 | Dark mode support via Tailwind `dark:` classes | M |
| 10.6 | Accessibility: keyboard navigation, focus management in modals | M |
| 10.7 | Comprehensive backend tests: full game lifecycle, edge cases | L |
| 10.8 | Frontend component tests with Vitest + React Testing Library | M |

**Deliverable**: Production-quality UX with robust error handling.

---

## 7. Testing Strategy

### Backend
- **pytest** + **pytest-asyncio** for async test support.
- **httpx.AsyncClient** to test endpoints without starting a server.
- **In-memory SQLite** per test for isolation.
- Factory helpers to create test games/players/rooms/weapons.

### Frontend
- **Vitest** + **React Testing Library** for component tests.

### What to Test Most

1. **Kill chain generation** (Phase 4): Circular chain is the heart of the game. Test with 3, 4, 5, 10, 20 players. Verify circularity and uniqueness.
2. **Death processing** (Phase 5): Chain inheritance through sequential deaths. Simulate full games. Verify winner detection.
3. **Auth/token validation**: Ensure players can only see their own assignments.

### What to Test Lightly

- Room/weapon CRUD (straightforward)
- UI rendering (basic smoke tests)
- Styling (manual inspection)

---

## Assumptions & Open Questions

### Assumptions

1. No persistent user accounts -- token-based identity per game.
2. 3+ players required to start.
3. No time limits -- game runs until one player remains.
4. Victim self-reports death (honor system).
5. No game pause -- once started, runs to completion.

### Open Questions

1. **Should the host be able to kick players from the lobby?**
2. **"Play Again" behavior** -- create new game with same players/rooms/weapons?
3. **Post-game visibility** -- should dead players see others' assignments after game over?
4. **Host disconnect** -- transfer host role to next player?
5. **Max player count?** -- Probably 4-20 for an Airbnb group.

---

## Dependencies

### Backend (`requirements.txt`)
```
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
sqlalchemy[asyncio]>=2.0.36
aiosqlite>=0.20.0
alembic>=1.14.0
pydantic-settings>=2.6.0
python-dotenv>=1.0.1
```

### Backend Dev
```
pytest>=8.3.0
pytest-asyncio>=0.24.0
httpx>=0.28.0
```

### Frontend (`package.json`)
```json
{
  "dependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "react-router-dom": "^7.0.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "tailwindcss": "^3.4.0",
    "typescript": "^5.6.0",
    "vite": "^6.0.0",
    "vitest": "^2.1.0",
    "@testing-library/react": "^16.0.0"
  }
}
```

---

## Phase Summary

| Phase | Name                          | Depends On | Est. Effort |
|-------|-------------------------------|------------|-------------|
| 0     | Project Scaffolding           | --         | Half day    |
| 1     | Data Models & Database        | Phase 0    | Half day    |
| 2     | Game Creation & Joining       | Phase 1    | 1 day       |
| 3     | Rooms & Weapons               | Phase 2    | Half day    |
| 4     | Game Start & Kill Chain       | Phase 3    | 1 day       |
| 5     | Death & Assignment Inheritance| Phase 4    | 1 day       |
| 6     | Frontend -- Home & Join       | Phase 0    | 1 day       |
| 7     | Frontend -- Lobby             | Phase 5, 6 | 1 day       |
| 8     | Frontend -- Game Page         | Phase 7    | 1 day       |
| 9     | Frontend -- Dead & Game Over  | Phase 8    | 1 day       |
| 10    | Polish & Hardening            | Phase 9    | 1 day       |

**Total: ~9 working days**

Note: Backend phases (0-5) and frontend Phase 6 can be done in parallel since the frontend can use mock data initially.
