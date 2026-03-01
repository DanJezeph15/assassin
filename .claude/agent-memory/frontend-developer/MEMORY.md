# Airbnb Games - Frontend Developer Memory

## Project Overview
Party game app (Assassin) for Airbnb stays. Mobile-first SPA. No user accounts -- token-based auth per game.

## Tech Stack
- React 19 + TypeScript + Vite 7 (SPA, no SSR/Next.js)
- Tailwind CSS v3 (utility-first, mobile-first)
- React Router v7 (`react-router-dom`, using `createBrowserRouter` + `RouterProvider`)
- State: React Context + useReducer (planned)
- Data: REST polling (no WebSockets)
- Backend: FastAPI on port 8000, proxied via Vite `/api`

## Project Structure
- Root: `/Users/dan/Documents/airbnb/games/`
- Frontend: `/Users/dan/Documents/airbnb/games/frontend/`
- Plan: `/Users/dan/Documents/airbnb/games/.claude/planning/project-plan.md`

## Frontend Directory Layout
```
frontend/src/
  main.tsx          # Entry point
  App.tsx           # RouterProvider wrapper
  routes.tsx        # createBrowserRouter route definitions
  index.css         # Tailwind directives only
  pages/            # HomePage, LobbyPage, GamePage, DeadPage, GameOverPage
  api/              # client.ts (ApiError), endpoints.ts (typed API calls)
  hooks/            # usePolling.ts
  components/       # Shared components
  components/ui/    # Button, Input, Card, Spinner, Badge, WarningIcon
  types/game.ts     # TS types mirroring backend
  utils/storage.ts  # localStorage helpers
```

## Design Tokens
- **Light bg**: `from-amber-50 via-orange-50 to-rose-50`
- **Dark bg**: `dark:from-gray-900 dark:via-gray-900 dark:to-gray-900`
- **Card**: `bg-white dark:bg-gray-800 shadow-lg shadow-gray-200/60 dark:shadow-black/20`
- **List rows**: `bg-gray-50 dark:bg-gray-700/50`
- **Dark mode**: `darkMode: "media"` in tailwind.config.js (system preference)
- **Body**: `class="bg-amber-50 dark:bg-gray-900"` on `<body>` in index.html

## UI Components
- **Button**: primary/secondary/danger, loading, dark mode with ring-offset
- **Input**: label, error, aria-invalid, dark mode bg/border/text
- **Card**: container with dark mode
- **Spinner**: inherits color, no dark-specific styles needed
- **Badge**: 4 colors, dark mode with /40 opacity backgrounds
- **WarningIcon**: shared warning triangle SVG (extracted from 5 files)
- **GameErrorCard**: 404 "Game not found" vs generic error, retry/home buttons

## usePolling Hook
- Returns `{ data, loading, error, errorStatus, refetch }`
- `errorStatus` exposes HTTP status (e.g., 404) from ApiError
- Stops polling on 404 and clears data to null so error UI renders
- `refetch()` resets interval timer
- Race condition guard via `requestCounterRef`

## Conventions
- `verbatimModuleSyntax` in tsconfig (use `import type`)
- ApiError class exposes `.status` and `.detail`
- `aria-live="polite"` on player counts only (NOT on Leaderboard -- too broad)
- DeadPage/GamePage use dark theme natively; dark: classes still applied for components
- Leaderboard has `theme` prop ("light" | "dark") for forced-dark contexts (DeadPage)
- All pages handle browser refresh via redirect effect (check game.status + is_alive)
- `navigating` state flag pattern to disable polling before redirect
- Always pass `onRetry={() => refetch()}` to GameErrorCard when using usePolling
- Avoid `!` non-null assertions on derived state -- use null guards with Spinner fallback
- Catch-all route `{ path: "*", element: <Navigate to="/" replace /> }` in routes.tsx

## Phase 10 (Polish) Completed
- WarningIcon extracted to shared component (was in 5 files)
- GameErrorCard created for consistent error display with 404 handling
- usePolling enhanced with errorStatus, auto-stop on 404, and data clearing
- Dark mode added to all UI primitives, all pages, all components
- Input validation verified: name 1-50 chars, room/weapon max 100 chars
- Double-submission prevention verified: all buttons disabled during loading
