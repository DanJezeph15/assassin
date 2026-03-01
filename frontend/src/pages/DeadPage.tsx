import { useCallback, useEffect, useMemo, useRef } from "react";
import { useNavigate, useParams } from "react-router-dom";
import Button from "../components/ui/Button";
import Spinner from "../components/ui/Spinner";
import GameErrorCard from "../components/GameErrorCard";
import Leaderboard from "../components/Leaderboard";
import { getGame } from "../api/endpoints";
import { getPlayerInfo, getPlayerToken } from "../utils/storage";
import usePolling from "../hooks/usePolling";

export default function DeadPage() {
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

  // Poll game state every 10 seconds to watch the game progress
  const fetchGameState = useCallback(
    () => getGame(gameCode),
    [gameCode],
  );
  const {
    data: game,
    loading: gameLoading,
    error: gameError,
    errorStatus: gameErrorStatus,
    refetch,
  } = usePolling(fetchGameState, 10000, !!gameCode && !!token);

  // Find current player in game data
  const currentPlayer = useMemo(() => {
    if (!game || !playerInfo) return null;
    return game.players.find((p) => p.id === playerInfo.id) ?? null;
  }, [game, playerInfo]);

  // Derive leaderboard from game.players (Leaderboard component owns sorting)
  const leaderboardEntries = useMemo(() => {
    if (!game) return null;
    return game.players.map((p) => ({
      name: p.name,
      kills: p.kills,
      is_alive: p.is_alive,
    }));
  }, [game]);

  // Player counts
  const aliveCount = useMemo(
    () => game?.players.filter((p) => p.is_alive).length ?? 0,
    [game],
  );
  const totalCount = game?.players.length ?? 0;

  // Redirect based on game status and player alive status (handles browser refresh)
  useEffect(() => {
    if (!game || !currentPlayer || navigatingRef.current) return;

    if (game.status === "lobby") {
      navigatingRef.current = true;
      navigate(`/game/${gameCode}`, { replace: true });
    } else if (game.status === "finished") {
      navigatingRef.current = true;
      navigate(`/game/${gameCode}/over`, { replace: true });
    } else if (currentPlayer.is_alive) {
      // Player is alive but on the dead page -- redirect to game
      navigatingRef.current = true;
      navigate(`/game/${gameCode}/play`, { replace: true });
    }
  }, [game, currentPlayer, gameCode, navigate]);

  // Don't render if no auth
  if (!token || !playerInfo) {
    return null;
  }

  // Initial loading state
  const isInitialLoad = gameLoading && !game;
  if (isInitialLoad) {
    return (
      <main className="min-h-dvh bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 px-4 py-8">
        <div className="mx-auto max-w-md space-y-6">
          {/* Elimination header skeleton */}
          <div className="text-center space-y-4 py-6 animate-pulse">
            <div className="w-20 h-20 rounded-full bg-gray-700 mx-auto" />
            <div className="h-8 w-56 bg-gray-700 rounded-lg mx-auto" />
            <div className="h-4 w-44 bg-gray-700 rounded-lg mx-auto" />
          </div>

          {/* Stats skeleton */}
          <div className="rounded-2xl bg-gray-800 p-6 animate-pulse">
            <div className="h-10 bg-gray-700 rounded-xl" />
          </div>

          {/* Leaderboard skeleton */}
          <div className="rounded-2xl bg-gray-800 p-6 animate-pulse">
            <div className="space-y-3">
              <div className="h-4 w-24 bg-gray-700 rounded-lg" />
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="h-10 bg-gray-700 rounded-xl"
                />
              ))}
            </div>
          </div>
        </div>
      </main>
    );
  }

  // Error state
  if (gameError && !game) {
    return (
      <main className="flex min-h-dvh flex-col items-center justify-center bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 px-4 py-8">
        <GameErrorCard
          errorStatus={gameErrorStatus}
          errorMessage={gameError}
          onRetry={() => refetch()}
          onGoHome={() => navigate("/")}
        />
      </main>
    );
  }

  return (
    <main className="min-h-dvh bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 px-4 py-8">
      <div className="mx-auto max-w-md space-y-6">
        {/* Elimination Header */}
        <div className="text-center space-y-4 py-4">
          {/* Skull / elimination icon */}
          <div className="relative inline-flex items-center justify-center">
            <div className="absolute inset-0 w-20 h-20 rounded-full bg-red-500/20 blur-xl" />
            <div className="relative w-20 h-20 rounded-full bg-gradient-to-br from-red-500/30 to-rose-600/30 border-2 border-red-500/40 flex items-center justify-center">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="w-10 h-10 text-red-400"
                aria-hidden="true"
              >
                <path d="M12 2a8 8 0 0 0-8 8c0 3.5 2 6 4 7.5V20h8v-2.5c2-1.5 4-4 4-7.5a8 8 0 0 0-8-8z" />
                <circle cx="9" cy="10" r="1.5" fill="currentColor" />
                <circle cx="15" cy="10" r="1.5" fill="currentColor" />
                <path d="M9 20v2h2v-1h2v1h2v-2" />
              </svg>
            </div>
          </div>

          <div className="space-y-2">
            <h1 className="text-3xl font-bold text-white tracking-tight">
              You Have Been Eliminated
            </h1>
            <p className="text-gray-400 text-base leading-relaxed">
              Your mission is over, {playerInfo.name}. Watch the remaining players battle it out.
            </p>
          </div>
        </div>

        {/* Spectator Mode Badge */}
        <div className="flex items-center justify-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gray-800 border border-gray-700">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500" />
            </span>
            <span className="text-sm font-medium text-gray-300">
              Spectating
            </span>
          </div>
        </div>

        {/* Players Alive Stats */}
        <div className="rounded-2xl bg-gray-800/80 border border-gray-700/50 p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-emerald-500/20 flex items-center justify-center">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                  className="w-4 h-4 text-emerald-400"
                  aria-hidden="true"
                >
                  <path d="M10 8a3 3 0 100-6 3 3 0 000 6zM3.465 14.493a1.23 1.23 0 00.41 1.412A9.957 9.957 0 0010 18c2.31 0 4.438-.784 6.131-2.1.43-.333.604-.903.408-1.41a7.002 7.002 0 00-13.074.003z" />
                </svg>
              </div>
              <span className="text-sm font-medium text-gray-400">
                Players Alive
              </span>
            </div>
            <div className="flex items-baseline gap-1" aria-live="polite">
              <span className="text-2xl font-bold text-white tabular-nums">
                {aliveCount}
              </span>
              <span className="text-sm text-gray-500">
                / {totalCount}
              </span>
            </div>
          </div>
        </div>

        {/* Live Leaderboard */}
        <div className="rounded-2xl bg-gray-800/80 border border-gray-700/50 p-6">
          {leaderboardEntries ? (
            <Leaderboard
              entries={leaderboardEntries}
              currentPlayerName={playerInfo.name}
              theme="dark"
            />
          ) : (
            <div className="flex items-center justify-center py-6">
              <Spinner className="h-6 w-6 text-gray-400" />
            </div>
          )}
        </div>

        {/* Home button */}
        <div className="pt-2">
          <Button
            variant="secondary"
            onClick={() => navigate("/")}
            className="w-full"
          >
            Leave Game
          </Button>
        </div>
      </div>
    </main>
  );
}
