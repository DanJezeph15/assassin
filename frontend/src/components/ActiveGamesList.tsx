import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import type { Game, GameStatus } from "../types/game";
import { getGame } from "../api/endpoints";
import { getUserGames, restoreSession } from "../api/auth";
import { ApiError } from "../api/client";
import {
  getAllGameSessions,
  getPlayerToken,
  removeGameSession,
  savePlayerInfo,
  savePlayerToken,
} from "../utils/storage";
import { useAuth } from "../context/AuthContext";
import { statusConfig } from "../utils/gameStatus";
import Card from "./ui/Card";

interface ResolvedGame {
  code: string;
  playerName: string;
  status: GameStatus;
  created_at: string;
}

export default function ActiveGamesList() {
  const navigate = useNavigate();
  const { authToken, user } = useAuth();
  const [games, setGames] = useState<ResolvedGame[]>([]);
  const [loading, setLoading] = useState(
    () => getAllGameSessions().length > 0 || !!authToken,
  );

  useEffect(() => {
    let cancelled = false;

    async function resolve() {
      const results: ResolvedGame[] = [];
      const seenCodes = new Set<string>();

      // 1. Resolve localStorage sessions (existing behavior)
      const sessions = getAllGameSessions();
      await Promise.all(
        sessions.map(async (session) => {
          try {
            const game: Game = await getGame(session.code);
            if (!cancelled) {
              seenCodes.add(game.code);
              results.push({
                code: game.code,
                playerName: session.playerInfo?.name ?? "Unknown",
                status: game.status,
                created_at: game.created_at,
              });
            }
          } catch (err) {
            if (err instanceof ApiError && err.status === 404) {
              removeGameSession(session.code);
            }
          }
        }),
      );

      // 2. If logged in, also fetch server-side games and merge
      if (authToken) {
        try {
          const response = await getUserGames(authToken);
          if (!cancelled) {
            // For each server game not in localStorage, restore the session
            await Promise.all(
              response.items.map(async (sg) => {
                // Only process games we don't already have locally
                if (seenCodes.has(sg.game_code)) return;

                // Restore session to get player token into localStorage
                const existingToken = getPlayerToken(sg.game_code);
                if (!existingToken) {
                  try {
                    const restored = await restoreSession(
                      authToken,
                      sg.game_code,
                    );
                    if (!cancelled) {
                      savePlayerToken(sg.game_code, restored.token);
                      savePlayerInfo(sg.game_code, {
                        id: restored.player_id,
                        name: restored.player_name,
                      });
                    }
                  } catch {
                    // Restore failed (game may be deleted) -- skip this game
                    return;
                  }
                }

                seenCodes.add(sg.game_code);
                results.push({
                  code: sg.game_code,
                  playerName: sg.player_name,
                  status: sg.game_status as GameStatus,
                  created_at: sg.created_at,
                });
              }),
            );
          }
        } catch {
          // Server games fetch failed -- still show localStorage games
        }
      }

      if (!cancelled) {
        results.sort(
          (a, b) =>
            new Date(b.created_at || 0).getTime() -
            new Date(a.created_at || 0).getTime(),
        );
        setGames(results);
        setLoading(false);
      }
    }

    const sessions = getAllGameSessions();
    if (sessions.length === 0 && !authToken) {
      return;
    }

    resolve();
    return () => {
      cancelled = true;
    };
  }, [authToken, user]);

  if (loading) {
    return (
      <Card>
        <div className="flex items-center justify-center py-4">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-gray-300 border-t-gray-600 dark:border-gray-600 dark:border-t-gray-300" />
          <span className="ml-3 text-sm text-gray-500 dark:text-gray-400">
            Loading your games...
          </span>
        </div>
      </Card>
    );
  }

  if (games.length === 0) return null;

  return (
    <Card>
      <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-4">
        Your Games
      </h2>
      <ul className="divide-y divide-gray-100 dark:divide-gray-800 -mx-6 sm:-mx-8">
        {games.map((game) => {
          const badge = statusConfig[game.status];
          return (
            <li key={game.code}>
              <button
                type="button"
                onClick={() =>
                  navigate(
                    game.status === "finished"
                      ? `/game/${game.code}/over`
                      : `/game/${game.code}`,
                  )
                }
                className="flex w-full items-center justify-between px-6 sm:px-8 py-3.5 text-left transition-colors hover:bg-gray-50 dark:hover:bg-gray-800/60"
              >
                <div className="min-w-0">
                  <div className="flex items-center gap-2.5">
                    <span className="font-mono text-sm font-semibold text-gray-900 dark:text-white tracking-wide">
                      {game.code}
                    </span>
                    <span
                      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${badge.classes}`}
                    >
                      {badge.label}
                    </span>
                  </div>
                  <p className="mt-0.5 text-sm text-gray-500 dark:text-gray-400 truncate">
                    {game.playerName}
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
      {authToken && (
        <div className="mt-3 text-center">
          <Link
            to="/my-games"
            className="text-sm text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 transition-colors"
          >
            View all games
          </Link>
        </div>
      )}
    </Card>
  );
}
