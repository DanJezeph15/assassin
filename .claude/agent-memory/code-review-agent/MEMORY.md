# Code Review Agent Memory - Airbnb Games

## Project Overview
- Party assassination game (like "Assassin" / "Killer") played in-person at an Airbnb
- Mobile-first SPA, no accounts, token-based ephemeral identity
- Project plan: `.claude/planning/project-plan.md`

## Tech Stack
- **Frontend**: React 19 + Vite 7 + TypeScript 5.9 + Tailwind 3.4 + React Router 7
- **Backend**: FastAPI + SQLAlchemy 2.0 (async) + SQLite + Alembic
- **No WebSockets**: REST polling only (game events are infrequent)

## Frontend Architecture Patterns
- `createBrowserRouter` (data router API) in routes.tsx
- Default export for page components; UI primitives extend native HTML attrs via `...rest`
- `apiClient<T>()` generic fetch wrapper with `ApiError` class (status + detail)
- localStorage keys: `assassin_token_{code}` and `assassin_player_{code}`
- Mobile: `min-h-dvh`, `text-base` inputs, `autoCapitalize="characters"` on code input
- Dark mode: `darkMode: "media"` in tailwind.config.js (system preference)
- DeadPage: always-dark theme (gray-900 gradient), no dark: prefix needed on that page
- GameOverPage: one-shot fetch via useEffect (no polling for finished games)
- `usePolling` hook: ref-based fetchFn, request counter for stale rejection, stops on 404

## Backend Architecture Patterns
- `lazy="selectin"` on all Game relationships
- Validation helpers: `validate_game_lobby()`, `validate_game_in_progress()`, `validate_game_membership()`
- Service functions raise HTTPException directly
- Token header: `X-Player-Token`

## Conventions
- Tailwind utility classes (no CSS modules)
- `from_attributes=True` via ConfigDict in Pydantic schemas
- Thin routers, business logic in services

## Review History (see `review-history.md` for full details)
- Phases 0-5: Backend issues all fixed (FK pragma, indexes, auth gap, etc.)
- Phase 6: Critical id mismatch fixed; API client Content-Type/204 fixed
- Phase 7: RoomList/WeaponList DRY resolved via EditableItemList; polling race fixed
- Phase 8: Racing navigation effects fixed; redundant leaderboard poll removed
- Phase 9: Double-sort, warning SVG duplication, one-shot fetch over-engineering
- Phase 10: WarningIcon extracted; GameErrorCard added; usePolling 404 stop; dark mode

## Phase 10 Key Issues Found
- Leaderboard in DeadPage: uses `dark:` classes but page is always-dark (light mode classes invisible)
- GameOverPage: `leaderboardEntries!` non-null assertion before null guard
- No catch-all route in routes.tsx (visiting /foo shows blank page)
- GamePage inline warning SVG not using WarningIcon (different SVG, minor DRY)
- `usePolling` doesn't clear `data` on error (stale data persists alongside error)
- GameErrorCard: `onRetry` sometimes missing, no retry on GamePage/DeadPage/GameOverPage error states
