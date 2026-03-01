import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import Spinner from "../components/ui/Spinner";
import AssignmentCard from "../components/AssignmentCard";
import DeathConfirmModal from "../components/DeathConfirmModal";
import Leaderboard from "../components/Leaderboard";
import GameErrorCard from "../components/GameErrorCard";
import { ApiError } from "../api/client";
import {
  confirmDeath,
  getAssignment,
  getGame,
} from "../api/endpoints";
import { getPlayerInfo, getPlayerToken } from "../utils/storage";
import usePolling from "../hooks/usePolling";

function AssignmentSkeleton() {
  return (
    <div className="rounded-2xl bg-gray-900 p-6 sm:p-8 animate-pulse">
      <div className="space-y-5">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gray-700" />
          <div className="h-3 w-24 bg-gray-700 rounded-lg" />
        </div>
        <div className="space-y-4">
          <div className="space-y-2">
            <div className="h-3 w-12 bg-gray-700 rounded" />
            <div className="h-8 w-40 bg-gray-700 rounded-lg" />
          </div>
          <div className="border-t border-gray-700" />
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <div className="h-3 w-10 bg-gray-700 rounded" />
              <div className="h-6 w-24 bg-gray-700 rounded-lg" />
            </div>
            <div className="space-y-2">
              <div className="h-3 w-14 bg-gray-700 rounded" />
              <div className="h-6 w-20 bg-gray-700 rounded-lg" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function GamePage() {
  const { code } = useParams<{ code: string }>();
  const navigate = useNavigate();
  const gameCode = code?.toUpperCase() ?? "";

  // Player identity from localStorage
  const token = getPlayerToken(gameCode);
  const playerInfo = getPlayerInfo(gameCode);

  // Modal state
  const [deathModalOpen, setDeathModalOpen] = useState(false);
  const [isConfirmingDeath, setIsConfirmingDeath] = useState(false);
  const [deathError, setDeathError] = useState("");

  // Navigating flag — disables polling once a redirect is triggered
  const [navigating, setNavigating] = useState(false);

  // Redirect to home if no token
  useEffect(() => {
    if (!token || !playerInfo) {
      navigate("/", { replace: true });
    }
  }, [token, playerInfo, navigate]);

  // Poll game state every 10 seconds
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
  } = usePolling(fetchGameState, 10000, !!gameCode && !!token && !navigating);

  // Poll assignment every 10 seconds (separate from game state)
  const fetchAssignment = useCallback(
    () => getAssignment(gameCode, token!),
    [gameCode, token],
  );
  const {
    data: assignment,
    loading: assignmentLoading,
  } = usePolling(fetchAssignment, 10000, !!gameCode && !!token && !navigating);

  // Check if current player is alive
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

  // Consolidated navigation effect with explicit priority
  useEffect(() => {
    if (!game || !currentPlayer) return;

    if (game.status === "lobby") {
      setNavigating(true);
      navigate(`/game/${gameCode}`, { replace: true });
    } else if (game.status === "finished") {
      setNavigating(true);
      navigate(`/game/${gameCode}/over`, { replace: true });
    } else if (!currentPlayer.is_alive) {
      setNavigating(true);
      navigate(`/game/${gameCode}/dead`, { replace: true });
    }
  }, [game, currentPlayer, gameCode, navigate]);

  // Death confirmation handler
  const handleConfirmDeath = useCallback(async () => {
    if (!token) return;
    setDeathError("");
    setIsConfirmingDeath(true);
    try {
      const result = await confirmDeath(gameCode, token);
      setDeathModalOpen(false);
      setNavigating(true);
      if (result.game_over) {
        navigate(`/game/${gameCode}/over`, { replace: true });
      } else {
        navigate(`/game/${gameCode}/dead`, { replace: true });
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setDeathError(err.detail);
      } else {
        setDeathError("Failed to confirm death. Please try again.");
      }
    } finally {
      setIsConfirmingDeath(false);
    }
  }, [token, gameCode, navigate]);

  // Don't render if no auth
  if (!token || !playerInfo) {
    return null;
  }

  // Initial loading state
  const isInitialLoad = gameLoading && !game;
  if (isInitialLoad) {
    return (
      <main className="min-h-dvh bg-gradient-to-br from-gray-100 via-gray-100 to-gray-200 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950 px-4 py-8">
        <div className="mx-auto max-w-md space-y-6">
          {/* Assignment skeleton */}
          <AssignmentSkeleton />

          {/* Death button skeleton */}
          <div className="h-12 bg-gray-200 dark:bg-gray-700 rounded-xl animate-pulse" />

          {/* Stats skeleton */}
          <Card>
            <div className="h-10 bg-gray-100 dark:bg-gray-700 rounded-xl animate-pulse" />
          </Card>

          {/* Leaderboard skeleton */}
          <Card>
            <div className="space-y-3 animate-pulse">
              <div className="h-4 w-24 bg-gray-200 dark:bg-gray-700 rounded-lg" />
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="h-10 bg-gray-100 dark:bg-gray-700 rounded-xl"
                />
              ))}
            </div>
          </Card>
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
          onRetry={() => refetch()}
          onGoHome={() => navigate("/")}
        />
      </main>
    );
  }

  return (
    <main className="min-h-dvh bg-gradient-to-br from-gray-100 via-gray-100 to-gray-200 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950 px-4 py-8">
      <div className="mx-auto max-w-md space-y-6">
        {/* Assignment Card */}
        {assignment ? (
          <AssignmentCard assignment={assignment} />
        ) : assignmentLoading ? (
          <AssignmentSkeleton />
        ) : (
          <Card className="text-center">
            <p className="text-gray-500 dark:text-gray-400">No assignment available</p>
          </Card>
        )}

        {/* Death Button */}
        <Button
          variant="danger"
          onClick={() => setDeathModalOpen(true)}
          className="w-full"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 20 20"
            fill="currentColor"
            className="w-5 h-5 mr-2 -ml-1"
            aria-hidden="true"
          >
            <path
              fillRule="evenodd"
              d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z"
              clipRule="evenodd"
            />
          </svg>
          I Have Been Killed
        </Button>

        {deathError && (
          <p className="text-sm text-red-500 dark:text-red-400 text-center" role="alert">
            {deathError}
          </p>
        )}

        {/* Player Stats */}
        <Card>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                  className="w-4 h-4 text-emerald-600 dark:text-emerald-400"
                  aria-hidden="true"
                >
                  <path d="M10 8a3 3 0 100-6 3 3 0 000 6zM3.465 14.493a1.23 1.23 0 00.41 1.412A9.957 9.957 0 0010 18c2.31 0 4.438-.784 6.131-2.1.43-.333.604-.903.408-1.41a7.002 7.002 0 00-13.074.003z" />
                </svg>
              </div>
              <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                Players Alive
              </span>
            </div>
            <div className="flex items-baseline gap-1" aria-live="polite">
              <span className="text-2xl font-bold text-gray-900 dark:text-white tabular-nums">
                {aliveCount}
              </span>
              <span className="text-sm text-gray-400 dark:text-gray-500">
                / {totalCount}
              </span>
            </div>
          </div>
        </Card>

        {/* Leaderboard */}
        <Card>
          {leaderboardEntries ? (
            <Leaderboard
              entries={leaderboardEntries}
              currentPlayerName={playerInfo?.name ?? null}
            />
          ) : (
            <div className="flex items-center justify-center py-6">
              <Spinner className="h-6 w-6 text-gray-400" />
            </div>
          )}
        </Card>
      </div>

      {/* Death Confirmation Modal */}
      <DeathConfirmModal
        open={deathModalOpen}
        loading={isConfirmingDeath}
        onConfirm={handleConfirmDeath}
        onCancel={() => {
          if (!isConfirmingDeath) {
            setDeathModalOpen(false);
            setDeathError("");
          }
        }}
      />
    </main>
  );
}
