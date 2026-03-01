# Review History - Detailed Notes

## Phase 6 Review (2026-02-28) - Frontend Home Page & Join Flow

### Files Reviewed
- `frontend/src/components/ui/Button.tsx` - Reusable button with variants, loading state
- `frontend/src/components/ui/Input.tsx` - Text input with label, error, aria
- `frontend/src/components/ui/Card.tsx` - Container component
- `frontend/src/api/client.ts` - Fetch wrapper with ApiError class
- `frontend/src/api/endpoints.ts` - createGame, joinGame, getGame typed functions
- `frontend/src/utils/storage.ts` - localStorage helpers for token/player info
- `frontend/src/types/game.ts` - TypeScript types mirroring backend schemas
- `frontend/src/pages/HomePage.tsx` - Create/join game page
- `frontend/src/routes.tsx` - React Router data router config
- `frontend/src/App.tsx` - RouterProvider wrapper
- `frontend/src/main.tsx` - Entry point
- `frontend/src/index.css` - Tailwind imports

### Issues Found
1. **CRITICAL**: Frontend types use `game_id`/`player_id` but backend sends `id` -- runtime undefined
2. **IMPORTANT**: Content-Type: application/json sent on GET requests
3. **IMPORTANT**: Dead branch in join error handling (400 and else do same thing)
4. **IMPORTANT**: apiClient fails on 204 No Content (always calls response.json())
5. **SUGGESTION**: Input id generation from label could collide -- use React.useId()
6. **SUGGESTION**: Game code input allows non-alphanumeric chars (spaces, symbols)
7. **SUGGESTION**: Inconsistent min-h-dvh vs min-h-screen across pages

### What Was Good
- Button loading state + disabled correctly prevents double-submit
- Input accessibility: aria-invalid, aria-describedby, role="alert", htmlFor
- ApiError class with status/detail for structured error handling
- Mobile-first: dvh, 3rem touch targets, text-base inputs, autoCapitalize
- localStorage namespacing and JSON.parse try/catch
- Client-side validation runs before API call, errors clear on change
- createBrowserRouter migration from deprecated BrowserRouter

## Phases 0-5 Review Summary
(Detailed notes were in the original MEMORY.md, consolidated here)

### Phase 0-1: Scaffolding + Data Models
- FK pragma moved to engine event listener
- Duplicate indexes removed
- GameStatus enum values_callable for lowercase DB values
- Migration: 860a6d704ebc_initial_schema.py

### Phase 2: Game Creation + Player Joining (17 tests)
- codes.py ambiguous char fix, whitespace validation moved to schema layer
- Service pattern: thin routers, logic in game_service.py
- First player becomes host via flush-then-set pattern

### Phase 3: Rooms & Weapons CRUD (50 tests)
- Cross-game auth gap found and fixed with validate_game_lobby()
- rooms.py and weapons.py nearly identical but acceptable

### Phase 4: Game Start & Kill Chain (76 tests)
- Kill chain: shuffle + modular arithmetic, provably correct
- Flush-not-commit contract for atomic game start
- DRY violation in start_game flagged

### Phase 5: Death & Assignment Inheritance (101 tests)
- 7-step death processing algorithm
- Missing (target_id, is_active) composite index
- No game_id filter in death service queries (defense-in-depth)
- DRY on validation helpers across 4+ endpoints

## Phase 9 Review (2026-02-28) - Frontend Dead & Game Over Pages

### Files Reviewed
- `frontend/src/pages/DeadPage.tsx` - Elimination page with spectator leaderboard
- `frontend/src/pages/GameOverPage.tsx` - Winner announcement and final leaderboard

### Issues Found
1. **IMPORTANT**: Double-sort of leaderboard entries -- parent pages sort before passing to Leaderboard component which re-sorts. Now in 3 pages + component (4 locations).
2. **IMPORTANT**: Unreachable spinner fallback for leaderboard on GameOverPage -- `leaderboardEntries` is derived from `game` which is guaranteed non-null after loading/error guards.
3. **IMPORTANT**: GameOverPage one-shot fetch uses `usePolling` + `hasFetched` state -- over-engineered, plain `useEffect` with cancellation would be clearer.
4. **SUGGESTION**: Warning triangle SVG now duplicated in 4+ page files (DeadPage, GameOverPage, GamePage, LobbyPage).
5. **SUGGESTION**: `playerInfo.name` used without optional chaining in DeadPage line 193 (inconsistent with GamePage pattern).
6. **SUGGESTION**: "Play Again" and "Home" buttons both navigate to "/" -- functionally identical.
7. **SUGGESTION**: Missing `aria-live="polite"` on alive count stats section for screen reader updates.

### What Was Good
- Redirect logic covers all game states (lobby, in_progress, finished, alive/dead) comprehensively
- `navigating` flag consistently disables polling before navigate() across all pages
- Leaderboard derived from game.players (no redundant API call) -- lesson from Phase 8 applied
- Winner determination: primary `alivePlayers.length === 1` with fallback to most kills
- Dark theme for DeadPage vs warm theme for GameOverPage -- good UX distinction
- Consistent `code?.toUpperCase() ?? ""` pattern across all game pages
- Skeleton loading states match actual page layout to prevent layout shift
- DeadPage polls at 10s (spectators want live updates), GameOverPage fetches once (static final state)
