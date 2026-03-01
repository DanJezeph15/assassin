import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import type { PaginatedUserGames } from "../types/auth";
import type { GameStatus } from "../types/game";
import { getUserGames, restoreSession } from "../api/auth";
import {
  getPlayerToken,
  savePlayerInfo,
  savePlayerToken,
} from "../utils/storage";
import { statusConfig } from "../utils/gameStatus";
import { useAuth } from "../context/AuthContext";
import Card from "../components/ui/Card";

export default function MyGamesPage() {
  const navigate = useNavigate();
  const { authToken, openAuthModal } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const page = Math.max(1, Number(searchParams.get("page")) || 1);

  const [data, setData] = useState<PaginatedUserGames | null>(null);
  const [error, setError] = useState("");
  const loading = !data && !error;

  // Redirect unauthenticated users
  useEffect(() => {
    if (!authToken) {
      openAuthModal();
      navigate("/", { replace: true });
    }
  }, [authToken, navigate, openAuthModal]);

  // Fetch games
  useEffect(() => {
    if (!authToken) return;

    let cancelled = false;

    async function fetchGames() {
      setData(null);
      setError("");
      try {
        const result = await getUserGames(authToken!, page);
        if (cancelled) return;

        // Restore sessions for games not in localStorage
        await Promise.all(
          result.items.map(async (game) => {
            const existingToken = getPlayerToken(game.game_code);
            if (existingToken) return;
            try {
              const restored = await restoreSession(authToken!, game.game_code);
              if (!cancelled) {
                savePlayerToken(game.game_code, restored.token);
                savePlayerInfo(game.game_code, {
                  id: restored.player_id,
                  name: restored.player_name,
                });
              }
            } catch {
              // Skip games that can't be restored
            }
          }),
        );

        if (!cancelled) {
          setData(result);
        }
      } catch {
        if (!cancelled) {
          setError("Failed to load games.");
        }
      }
    }

    fetchGames();
    return () => {
      cancelled = true;
    };
  }, [authToken, page]);

  if (!authToken) return null;

  return (
    <main className="flex min-h-dvh flex-col items-center bg-gradient-to-br from-gray-100 via-gray-100 to-gray-200 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950 px-4 py-8">
      <div className="w-full max-w-lg space-y-6">
        {/* Header */}
        <header className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => navigate("/")}
            className="inline-flex items-center justify-center w-9 h-9 rounded-xl text-gray-500 dark:text-gray-400 hover:bg-white/60 dark:hover:bg-gray-800/60 transition-colors"
            aria-label="Back to home"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
              <path fillRule="evenodd" d="M11.78 5.22a.75.75 0 0 1 0 1.06L8.06 10l3.72 3.72a.75.75 0 1 1-1.06 1.06l-4.25-4.25a.75.75 0 0 1 0-1.06l4.25-4.25a.75.75 0 0 1 1.06 0Z" clipRule="evenodd" />
            </svg>
          </button>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white tracking-tight">
            My Games
          </h1>
        </header>

        {/* Loading */}
        {loading && (
          <Card>
            <div className="flex items-center justify-center py-4">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-gray-300 border-t-gray-600 dark:border-gray-600 dark:border-t-gray-300" />
              <span className="ml-3 text-sm text-gray-500 dark:text-gray-400">
                Loading your games...
              </span>
            </div>
          </Card>
        )}

        {/* Error */}
        {error && (
          <Card>
            <p className="text-sm text-red-500 dark:text-red-400 text-center py-2">
              {error}
            </p>
          </Card>
        )}

        {/* Empty state */}
        {!loading && !error && data && data.items.length === 0 && data.total === 0 && (
          <Card>
            <div className="text-center py-6">
              <p className="text-gray-500 dark:text-gray-400">
                You haven't joined any games yet.
              </p>
              <button
                type="button"
                onClick={() => navigate("/")}
                className="mt-3 text-sm text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 transition-colors"
              >
                Create or join a game
              </button>
            </div>
          </Card>
        )}

        {/* Game list */}
        {!loading && !error && data && data.items.length > 0 && (
          <Card>
            <ul className="divide-y divide-gray-100 dark:divide-gray-800 -mx-6 sm:-mx-8">
              {data.items.map((game) => {
                const badge = statusConfig[game.game_status as GameStatus] ?? statusConfig.lobby;
                return (
                  <li key={game.game_id}>
                    <button
                      type="button"
                      onClick={() =>
                        navigate(
                          game.game_status === "finished"
                            ? `/game/${game.game_code}/over`
                            : `/game/${game.game_code}`,
                        )
                      }
                      className="flex w-full items-center justify-between px-6 sm:px-8 py-3.5 text-left transition-colors hover:bg-gray-50 dark:hover:bg-gray-800/60"
                    >
                      <div className="min-w-0">
                        <div className="flex items-center gap-2.5">
                          <span className="font-mono text-sm font-semibold text-gray-900 dark:text-white tracking-wide">
                            {game.game_code}
                          </span>
                          <span
                            className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${badge.classes}`}
                          >
                            {badge.label}
                          </span>
                        </div>
                        <p className="mt-0.5 text-sm text-gray-500 dark:text-gray-400 truncate">
                          {game.player_name}
                        </p>
                      </div>
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                        className="h-5 w-5 flex-shrink-0 text-gray-400 dark:text-gray-500"
                        aria-hidden="true"
                      >
                        <path
                          fillRule="evenodd"
                          d="M8.22 5.22a.75.75 0 0 1 1.06 0l4.25 4.25a.75.75 0 0 1 0 1.06l-4.25 4.25a.75.75 0 0 1-1.06-1.06L11.94 10 8.22 6.28a.75.75 0 0 1 0-1.06Z"
                          clipRule="evenodd"
                        />
                      </svg>
                    </button>
                  </li>
                );
              })}
            </ul>
          </Card>
        )}

        {/* Pagination */}
        {!loading && !error && data && data.pages > 1 && (
          <div className="flex items-center justify-between">
            <button
              type="button"
              disabled={page <= 1}
              onClick={() => setSearchParams({ page: String(page - 1) })}
              className="px-4 py-2 text-sm font-medium rounded-xl transition-colors disabled:opacity-40 disabled:cursor-not-allowed text-gray-600 dark:text-gray-400 hover:bg-white/60 dark:hover:bg-gray-800/60"
            >
              Previous
            </button>
            <span className="text-sm text-gray-500 dark:text-gray-400">
              Page {page} of {data.pages}
            </span>
            <button
              type="button"
              disabled={page >= data.pages}
              onClick={() => setSearchParams({ page: String(page + 1) })}
              className="px-4 py-2 text-sm font-medium rounded-xl transition-colors disabled:opacity-40 disabled:cursor-not-allowed text-gray-600 dark:text-gray-400 hover:bg-white/60 dark:hover:bg-gray-800/60"
            >
              Next
            </button>
          </div>
        )}
      </div>
    </main>
  );
}
