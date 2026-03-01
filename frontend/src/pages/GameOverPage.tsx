import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import Spinner from "../components/ui/Spinner";
import GameErrorCard from "../components/GameErrorCard";
import Leaderboard from "../components/Leaderboard";
import { ApiError } from "../api/client";
import { getGame } from "../api/endpoints";
import { getPlayerInfo, getPlayerToken } from "../utils/storage";
import type { Game } from "../types/game";

export default function GameOverPage() {
  const { code } = useParams<{ code: string }>();
  const navigate = useNavigate();
  const gameCode = code?.toUpperCase() ?? "";

  // Player identity from localStorage
  const token = getPlayerToken(gameCode);
  const playerInfo = getPlayerInfo(gameCode);

  // Navigating flag -- prevents duplicate redirects
  const navigatingRef = useRef(false);

  // Redirect to home if no token
  useEffect(() => {
    if (!token || !playerInfo) {
      navigate("/", { replace: true });
    }
  }, [token, playerInfo, navigate]);

  // Fetch game state once on mount
  const [game, setGame] = useState<Game | null>(null);
  const [gameLoading, setGameLoading] = useState(true);
  const [gameError, setGameError] = useState<string | null>(null);
  const [gameErrorStatus, setGameErrorStatus] = useState<number | null>(null);

  useEffect(() => {
    if (!gameCode || !token || navigatingRef.current) return;
    let cancelled = false;
    getGame(gameCode)
      .then((data) => {
        if (!cancelled) { setGame(data); setGameError(null); setGameErrorStatus(null); }
      })
      .catch((err) => {
        if (!cancelled) {
          setGameError(err instanceof Error ? err.message : "Something went wrong");
          setGameErrorStatus(err instanceof ApiError ? err.status : null);
        }
      })
      .finally(() => {
        if (!cancelled) setGameLoading(false);
      });
    return () => { cancelled = true; };
  }, [gameCode, token]);

  // Find current player
  const currentPlayer = useMemo(() => {
    if (!game || !playerInfo) return null;
    return game.players.find((p) => p.id === playerInfo.id) ?? null;
  }, [game, playerInfo]);

  // Determine the winner (last alive player)
  const winner = useMemo(() => {
    if (!game) return null;
    const alivePlayers = game.players.filter((p) => p.is_alive);
    if (alivePlayers.length === 1) return alivePlayers[0];
    // Fallback: player with most kills
    if (game.players.length === 0) return null;
    return [...game.players].sort((a, b) => b.kills - a.kills)[0];
  }, [game]);

  const isWinner = !!(winner && playerInfo && winner.id === playerInfo.id);

  // Derive leaderboard from game.players (Leaderboard component owns sorting)
  const leaderboardEntries = useMemo(() => {
    if (!game) return null;
    return game.players.map((p) => ({
      name: p.name,
      kills: p.kills,
      is_alive: p.is_alive,
    }));
  }, [game]);

  // Redirect based on game status (handles browser refresh)
  useEffect(() => {
    if (!game || !currentPlayer || navigatingRef.current) return;

    if (game.status === "lobby") {
      navigatingRef.current = true;
      navigate(`/game/${gameCode}`, { replace: true });
    } else if (game.status === "in_progress") {
      navigatingRef.current = true;
      if (currentPlayer.is_alive) {
        navigate(`/game/${gameCode}/play`, { replace: true });
      } else {
        navigate(`/game/${gameCode}/dead`, { replace: true });
      }
    }
  }, [game, currentPlayer, gameCode, navigate]);

  // Don't render if no auth
  if (!token || !playerInfo) {
    return null;
  }

  // Loading state
  const isInitialLoad = gameLoading && !game;
  if (isInitialLoad) {
    return (
      <main className="min-h-dvh bg-gradient-to-br from-gray-100 via-gray-100 to-gray-200 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950 px-4 py-8">
        <div className="mx-auto max-w-md flex flex-col items-center justify-center min-h-[80dvh]">
          <Spinner className="h-8 w-8 text-red-700" />
        </div>
      </main>
    );
  }

  // Error state
  if (gameError && !game) {
    return (
      <main className="flex min-h-dvh flex-col items-center justify-center bg-gradient-to-br from-gray-100 via-gray-100 to-gray-200 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950 px-4 py-8">
        <GameErrorCard
          errorStatus={gameErrorStatus}
          errorMessage={gameError}
          onGoHome={() => navigate("/")}
        />
      </main>
    );
  }

  return (
    <main className="min-h-dvh bg-gradient-to-br from-gray-100 via-gray-100 to-gray-200 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950 px-4 py-8">
      <div className="mx-auto max-w-md space-y-6">
        {/* Winner Announcement */}
        <div className="text-center space-y-5 py-4">
          {/* Trophy / celebration icon */}
          <div className="relative inline-flex items-center justify-center">
            {/* Decorative glow */}
            <div className="absolute inset-0 w-24 h-24 rounded-full bg-red-700/30 blur-2xl" />
            <div className="relative w-24 h-24 rounded-full bg-gradient-to-br from-red-700 to-red-900 shadow-xl shadow-red-300/50 dark:shadow-red-900/30 flex items-center justify-center">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="w-12 h-12 text-white"
                aria-hidden="true"
              >
                <path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6" />
                <path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18" />
                <path d="M4 22h16" />
                <path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22" />
                <path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22" />
                <path d="M18 2H6v7a6 6 0 0 0 12 0V2Z" />
              </svg>
            </div>
          </div>

          <div className="space-y-2">
            <p className="text-sm font-semibold text-red-700 dark:text-red-400 uppercase tracking-wider">
              Game Over
            </p>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white tracking-tight">
              {isWinner ? "You Win!" : "We Have a Winner"}
            </h1>
          </div>

          {/* Winner name card */}
          {winner && (
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-br from-red-700/20 to-red-900/20 rounded-2xl blur-sm" />
              <div className="relative rounded-2xl bg-white dark:bg-gray-900 border-2 border-red-300 dark:border-red-700 shadow-lg shadow-red-100 dark:shadow-red-900/20 px-6 py-5">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                  Last One Standing
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {winner.name}
                </p>
                <div className="flex items-center justify-center gap-3 mt-3">
                  <span className="inline-flex items-center gap-1 text-sm text-red-700 dark:text-red-400 font-medium">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                      className="w-4 h-4"
                      aria-hidden="true"
                    >
                      <path
                        fillRule="evenodd"
                        d="M10.868 2.884c-.321-.772-1.415-.772-1.736 0l-1.83 4.401-4.753.381c-.833.067-1.171 1.107-.536 1.651l3.62 3.102-1.106 4.637c-.194.813.691 1.456 1.405 1.02L10 15.591l4.069 2.485c.713.436 1.598-.207 1.404-1.02l-1.106-4.637 3.62-3.102c.635-.544.297-1.584-.536-1.65l-4.752-.382-1.831-4.401z"
                        clipRule="evenodd"
                      />
                    </svg>
                    {winner.kills} {winner.kills === 1 ? "kill" : "kills"}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Personal message */}
          {isWinner ? (
            <p className="text-gray-500 dark:text-gray-400 text-base leading-relaxed">
              Congratulations, {playerInfo.name}! You outwitted and outlasted everyone.
            </p>
          ) : (
            <p className="text-gray-500 dark:text-gray-400 text-base leading-relaxed">
              Great game, everyone! {winner?.name} proved to be the ultimate assassin.
            </p>
          )}
        </div>

        {/* Final Leaderboard */}
        <Card>
          {leaderboardEntries ? (
            <Leaderboard entries={leaderboardEntries} currentPlayerName={playerInfo.name} />
          ) : (
            <div className="flex items-center justify-center py-6">
              <Spinner className="h-6 w-6 text-red-700" />
            </div>
          )}
        </Card>

        {/* Action Button */}
        <div className="pt-2">
          <Button
            onClick={() => navigate("/")}
            className="w-full"
          >
            Play Again
          </Button>
        </div>
      </div>
    </main>
  );
}
