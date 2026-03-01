# Architect Planner Memory

## Project: Airbnb Games

### Tech Stack Decisions (Confirmed in Planning)
- **Backend**: FastAPI + SQLAlchemy 2.0 async + aiosqlite
- **Database**: SQLite (not PostgreSQL) -- justified by small data model, no concurrent write pressure, zero-infrastructure deployment
- **Frontend**: React 19 + Vite + TypeScript + Tailwind CSS
- **Real-time**: WebSockets via FastAPI/Starlette (not SSE, not polling)
- **Auth**: Token-based (random token per player, no user accounts)
- **State management**: React Context + useReducer (no Redux/Zustand needed)

### Key Architecture Patterns
- REST endpoints for all actions (create, join, add room, start, confirm death)
- WebSockets used purely for server-to-client broadcasting (not for sending actions)
- Player identity via random token stored in localStorage, sent as header on REST / as URL param on WebSocket
- ConnectionManager pattern: dict of game_code -> set[WebSocket] for broadcasting
- Private vs broadcast messages: assignments are private to the player, deaths are broadcast

### Project Structure
- Plan lives at: `.claude/planning/project-plan.md`
- Backend at: `backend/app/` with models/, schemas/, routers/, services/, websocket/
- Frontend at: `frontend/src/` with pages/, components/, hooks/, context/, api/, types/

### Game: Assassin
- Circular kill chain: A->B->C->...->A
- On death: killer inherits victim's assignment (target, room, weapon)
- Minimum 3 players, >= 1 room, >= 1 weapon to start
- Only victim can confirm their own death
- Game ends when 1 player remains

### Open Questions (Unresolved)
- Host disconnection handling (transfer host role?)
- Play Again feature (exact behavior?)
- Post-game assignment reveal for dead players?
- Maximum player count cap?
