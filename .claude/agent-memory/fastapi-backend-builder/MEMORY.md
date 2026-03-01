# Airbnb Games - Backend Builder Memory

## Project Overview
Party game app (Assassin) for Airbnb stays. REST-only FastAPI + SQLite backend, React frontend.

## Key Paths
- Project root: `/Users/dan/Documents/airbnb/games/`
- Backend: `/Users/dan/Documents/airbnb/games/backend/`
- Python venv: `/Users/dan/Documents/airbnb/games/.venv/` (Python 3.12)
- Run pip: `/Users/dan/Documents/airbnb/games/.venv/bin/python -m pip` (no pip binary directly)
- DB file: `/Users/dan/Documents/airbnb/games/backend/games.db`
- Plan: `/Users/dan/Documents/airbnb/games/.claude/planning/project-plan.md`

## Architecture
- FastAPI app at `backend/app/main.py`, run with `uvicorn app.main:app --reload` from backend/
- Config via Pydantic BaseSettings in `backend/app/config.py`
- Async SQLAlchemy 2.0 with aiosqlite in `backend/app/database.py`
- Alembic for migrations: `backend/alembic/` with `backend/alembic.ini`
- Models use UUID PKs, mapped_column, Mapped types
- `render_as_batch=True` in Alembic env.py for SQLite ALTER TABLE support
- Game.host_id uses `use_alter=True` due to circular FK with players table

## Completed Phases
- Phase 0: Backend scaffolding (directory structure, config, database, main.py, health endpoint)
- Phase 1: All 5 data models (Game, Player, Room, Weapon, Assignment), initial migration generated and applied
- Phase 2: Game creation, player joining, auth dependency, 18 tests passing
- Phase 3: Rooms & Weapons CRUD (add/remove rooms and weapons), 54 total tests passing (includes cross-game auth fix)
- Phase 4: Game start & kill chain generation, 76 total tests passing (22 new)
- Phase 5: Death & assignment inheritance, 101 total tests passing (25 new)

## Models Summary
- Game: id, code(6), status(enum), host_id(FK->players), created_at, updated_at
- Player: id, game_id(FK), name(50), is_alive, kills, token(64), joined_at
- Room: id, game_id(FK), name(100)
- Weapon: id, game_id(FK), name(100)
- Assignment: id, game_id(FK), killer_id(FK), target_id(FK), room_id(FK), weapon_id(FK), is_active, created_at

## Important Patterns
- GameStatus enum: LOBBY, IN_PROGRESS, FINISHED (stored as varchar, native_enum=False)
- All relationships use lazy="selectin" on the Game model (eager load collections)
- Composite indexes: (killer_id, is_active) and (game_id, is_active) on assignments
- lifespan handler uses `conn.run_sync(Base.metadata.create_all)` (not `conn.create_all`)

## Phase 2 Key Files
- `backend/app/utils/codes.py` - game code generator (6-char alphanum, checks DB uniqueness)
- `backend/app/schemas/game.py` - GameCreate, GameResponse, GameDetail (with inline PlayerInfo, RoomInfo, WeaponInfo)
- `backend/app/schemas/player.py` - PlayerJoin, PlayerResponse, PlayerWithToken
- `backend/app/dependencies.py` - get_db (async session), get_current_player (X-Player-Token header auth)
- `backend/app/services/game_service.py` - create_game, get_game_by_code, validate_game_lobby, join_game (module-level functions, no class)
- `backend/app/routers/games.py` - POST /api/games (201), GET /api/games/{code}
- `backend/app/routers/players.py` - POST /api/games/{code}/players (201)

## Important Patterns
- GameStatus enum: LOBBY, IN_PROGRESS, FINISHED (stored as varchar, native_enum=False)
- All relationships use lazy="selectin" on the Game model (eager load collections)
- Composite indexes: (killer_id, is_active) and (game_id, is_active) on assignments
- lifespan handler uses `conn.run_sync(Base.metadata.create_all)` (not `conn.create_all`)
- Services use module-level async functions (not classes), receive AsyncSession directly
- Player auth via X-Player-Token header, token is secrets.token_hex(32) = 64 chars
- First player to join becomes host (game.host_id set after db.flush() to get player.id)
- Name uniqueness is case-insensitive, names are stripped of whitespace
- Game code lookup is case-insensitive (uppercased in service)

## Phase 3 Key Files
- `backend/app/schemas/room.py` - RoomCreate (name, strip whitespace validator), RoomResponse (id, name)
- `backend/app/schemas/weapon.py` - WeaponCreate, WeaponResponse (mirrors room schemas)
- `backend/app/routers/rooms.py` - POST /api/games/{code}/rooms (201), DELETE /api/games/{code}/rooms/{room_id} (204)
- `backend/app/routers/weapons.py` - POST /api/games/{code}/weapons (201), DELETE /api/games/{code}/weapons/{weapon_id} (204)
- `backend/tests/test_rooms_weapons.py` - 32 tests for rooms/weapons CRUD, auth, validation
- Room/weapon CRUD validates: lobby status, player-game membership (403), case-insensitive duplicate names, auth token, belongs-to-game on delete
- `validate_game_lobby(db, code, player)` centralizes game fetch + lobby check + player membership check; used by rooms & weapons routers

## Phase 4 Key Files
- `backend/app/schemas/assignment.py` - AssignmentResponse (target_name, room_name, weapon_name)
- `backend/app/services/assignment_service.py` - generate_kill_chain(db, game): shuffles players into circular chain, random room/weapon per assignment
- `backend/app/routers/games.py` - now includes POST /api/games/{code}/start (200) and GET /api/games/{code}/assignment
- `backend/tests/test_assignments.py` - 22 tests: start validation, chain circularity (3/5/10 players), assignment content, auth edge cases
- Start game validates: host-only (403), lobby status (400), >=3 players (400), >=1 room (400), >=1 weapon (400)
- Kill chain: random.shuffle for player order, random.choice for room/weapon, circular ring via modular index
- GET /assignment: joins Assignment -> target Player, Room, Weapon via selectinload, returns 404 if no active assignment

## Phase 5 Key Files
- `backend/app/services/death_service.py` - process_death(db, victim): marks dead, finds killer via active assignment targeting victim, increments kills, deactivates both assignments, creates new assignment for killer inheriting victim's target/room/weapon, checks game over
- `backend/app/schemas/death.py` - DeathResponse (killer_name, kill_count, game_over, winner_name), LeaderboardEntry (name, kills, is_alive)
- `backend/app/routers/games.py` - now also includes POST /api/games/{code}/deaths (200) and GET /api/games/{code}/leaderboard
- `backend/tests/test_death.py` - 25 tests: single death, chain inheritance, sequential deaths (3/5/10 players), game over detection, leaderboard sorting, edge cases
- Death validates: player belongs to game (403), game is IN_PROGRESS (400), player is_alive (400)
- Leaderboard: sorted by kills desc, name asc; includes dead players
- death_service uses db.flush(), router does db.commit() (same pattern as assignment_service)
- Game over: when alive_count == 1, set game.status = FINISHED and deactivate winner's assignment

## Testing
- pytest with asyncio_mode="auto" configured in pyproject.toml
- Tests in backend/tests/
- conftest.py: in-memory SQLite, autouse setup_database fixture (create/drop tables per test)
- Must disable FK checks during drop_all due to circular games.host_id -> players FK
- httpx AsyncClient with ASGITransport for endpoint tests
- Dependency override: app.dependency_overrides[get_db] for test DB session
- Helper pattern: `create_game_and_join(client, name)` returns (code, token) for test setup
