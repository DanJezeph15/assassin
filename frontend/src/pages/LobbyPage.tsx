import { useCallback, useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import { useNavigate, useParams } from "react-router-dom";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import GameCodeDisplay from "../components/GameCodeDisplay";
import PlayerList from "../components/PlayerList";
import RoomList from "../components/RoomList";
import WeaponList from "../components/WeaponList";
import GameErrorCard from "../components/GameErrorCard";
import { ApiError } from "../api/client";
import { getGame, joinGame, startGame } from "../api/endpoints";
import {
  getPlayerInfo,
  getPlayerToken,
  savePlayerInfo,
  savePlayerToken,
} from "../utils/storage";
import { useAuth } from "../context/AuthContext";
import usePolling from "../hooks/usePolling";

export default function LobbyPage() {
  const { code } = useParams<{ code: string }>();
  const navigate = useNavigate();
  const { authToken, openAuthModal } = useAuth();
  const gameCode = code?.toUpperCase() ?? "";

  // Player identity from localStorage
  const [token, setToken] = useState<string | null>(() =>
    getPlayerToken(gameCode),
  );
  const [playerInfo, setPlayerInfo] = useState(() =>
    getPlayerInfo(gameCode),
  );

  // Join form state (shown when no token)
  const [joinName, setJoinName] = useState("");
  const [isJoining, setIsJoining] = useState(false);
  const [joinNameError, setJoinNameError] = useState("");
  const [joinError, setJoinError] = useState("");

  // Start game state
  const [isStarting, setIsStarting] = useState(false);
  const [startError, setStartError] = useState("");

  // Polling for game state
  const fetchGame = useCallback(() => getGame(gameCode), [gameCode]);
  const { data: game, loading, error: pollError, errorStatus: pollErrorStatus, refetch } = usePolling(
    fetchGame,
    5000,
    !!gameCode,
  );

  // Auto-navigate when game status changes to in_progress
  useEffect(() => {
    if (game?.status === "in_progress") {
      navigate(`/game/${gameCode}/play`, { replace: true });
    } else if (game?.status === "finished") {
      navigate(`/game/${gameCode}/over`, { replace: true });
    }
  }, [game?.status, gameCode, navigate]);

  // Derived state
  const isHost = useMemo(
    () => !!(playerInfo && game && game.host_id === playerInfo.id),
    [playerInfo, game],
  );

  const canStart = useMemo(() => {
    if (!game) return false;
    return (
      game.players.length >= 3 &&
      game.rooms.length >= 1 &&
      game.weapons.length >= 1
    );
  }, [game]);

  const startDisabledReason = useMemo(() => {
    if (!game) return "";
    const reasons: string[] = [];
    if (game.players.length < 3) {
      const needed = 3 - game.players.length;
      reasons.push(`${needed} more player${needed === 1 ? "" : "s"} needed`);
    }
    if (game.rooms.length < 1) reasons.push("at least 1 room needed");
    if (game.weapons.length < 1) reasons.push("at least 1 weapon needed");
    return reasons.length > 0 ? reasons.join(", ") : "";
  }, [game]);

  // Join game handler
  async function handleJoin(e: FormEvent) {
    e.preventDefault();

    if (!authToken) {
      openAuthModal();
      return;
    }

    setJoinNameError("");
    setJoinError("");

    const trimmedName = joinName.trim();
    if (!trimmedName) {
      setJoinNameError("Enter your name");
      return;
    }
    if (trimmedName.length > 50) {
      setJoinNameError("Name must be 50 characters or less");
      return;
    }

    setIsJoining(true);
    try {
      const result = await joinGame(gameCode, trimmedName, authToken);
      savePlayerToken(gameCode, result.token);
      savePlayerInfo(gameCode, { id: result.id, name: result.name });
      setToken(result.token);
      setPlayerInfo({ id: result.id, name: result.name });
      refetch();
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.detail.toLowerCase().includes("name")) {
          setJoinNameError(err.detail);
        } else {
          setJoinError(err.detail);
        }
      } else {
        setJoinError("Failed to join game. Please try again.");
      }
    } finally {
      setIsJoining(false);
    }
  }

  // Start game handler
  async function handleStartGame() {
    if (!token) return;
    setStartError("");
    setIsStarting(true);
    try {
      await startGame(gameCode, token);
      refetch();
    } catch (err) {
      if (err instanceof ApiError) {
        setStartError(err.detail);
      } else {
        setStartError("Failed to start game. Please try again.");
      }
    } finally {
      setIsStarting(false);
    }
  }

  // Loading skeleton for first load
  if (loading && !game) {
    return (
      <main className="min-h-dvh bg-gradient-to-br from-gray-100 via-gray-100 to-gray-200 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950 px-4 py-8">
        <div className="mx-auto max-w-md space-y-6">
          {/* Code skeleton */}
          <Card>
            <div className="space-y-3 animate-pulse">
              <div className="h-4 w-24 bg-gray-200 dark:bg-gray-700 rounded-lg mx-auto" />
              <div className="h-10 w-48 bg-gray-200 dark:bg-gray-700 rounded-lg mx-auto" />
              <div className="h-3 w-56 bg-gray-200 dark:bg-gray-700 rounded-lg mx-auto" />
            </div>
          </Card>

          {/* Players skeleton */}
          <Card>
            <div className="space-y-3 animate-pulse">
              <div className="flex items-center justify-between">
                <div className="h-4 w-16 bg-gray-200 dark:bg-gray-700 rounded-lg" />
                <div className="h-4 w-20 bg-gray-200 dark:bg-gray-700 rounded-lg" />
              </div>
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="flex items-center gap-2 px-3 py-2.5 rounded-xl bg-gray-50 dark:bg-gray-700/50"
                >
                  <div className="w-8 h-8 bg-gray-200 dark:bg-gray-700 rounded-full" />
                  <div className="h-4 w-24 bg-gray-200 dark:bg-gray-700 rounded-lg" />
                </div>
              ))}
            </div>
          </Card>

          {/* Rooms skeleton */}
          <Card>
            <div className="space-y-3 animate-pulse">
              <div className="flex items-center justify-between">
                <div className="h-4 w-14 bg-gray-200 dark:bg-gray-700 rounded-lg" />
                <div className="h-4 w-16 bg-gray-200 dark:bg-gray-700 rounded-lg" />
              </div>
              <div className="h-12 bg-gray-100 dark:bg-gray-700 rounded-xl" />
            </div>
          </Card>

          {/* Weapons skeleton */}
          <Card>
            <div className="space-y-3 animate-pulse">
              <div className="flex items-center justify-between">
                <div className="h-4 w-20 bg-gray-200 dark:bg-gray-700 rounded-lg" />
                <div className="h-4 w-20 bg-gray-200 dark:bg-gray-700 rounded-lg" />
              </div>
              <div className="h-12 bg-gray-100 dark:bg-gray-700 rounded-xl" />
            </div>
          </Card>
        </div>
      </main>
    );
  }

  // Error state (game not found or network error)
  if (pollError && !game) {
    return (
      <main className="flex min-h-dvh flex-col items-center justify-center bg-gradient-to-br from-gray-100 via-gray-100 to-gray-200 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950 px-4 py-8">
        <GameErrorCard
          errorStatus={pollErrorStatus}
          errorMessage={pollError}
          onRetry={() => refetch()}
          onGoHome={() => navigate("/")}
        />
      </main>
    );
  }

  // If no token, show join form
  if (!token || !playerInfo) {
    return (
      <main className="flex min-h-dvh flex-col items-center justify-center bg-gradient-to-br from-gray-100 via-gray-100 to-gray-200 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950 px-4 py-8">
        <div className="w-full max-w-md space-y-6">
          {game && (
            <Card>
              <GameCodeDisplay code={game.code} />
            </Card>
          )}

          <Card>
            <form onSubmit={handleJoin} className="space-y-4" noValidate>
              <div className="text-center">
                <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">
                  Join this game
                </h2>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  Enter your name to join the lobby
                </p>
              </div>

              <Input
                label="Your Name"
                placeholder="Enter your name"
                value={joinName}
                onChange={(e) => {
                  setJoinName(e.target.value);
                  setJoinNameError("");
                }}
                error={joinNameError}
                maxLength={50}
                autoComplete="off"
                autoFocus
              />

              <Button
                type="submit"
                loading={isJoining}
                className="w-full"
              >
                Join Game
              </Button>

              {joinError && (
                <p className="text-sm text-red-500 dark:text-red-400 text-center" role="alert">
                  {joinError}
                </p>
              )}
            </form>
          </Card>

          {/* Show current player list even before joining */}
          {game && game.players.length > 0 && (
            <Card>
              <PlayerList
                players={game.players}
                hostId={game.host_id}
                currentPlayerId={null}
              />
            </Card>
          )}
        </div>
      </main>
    );
  }

  // Main lobby view (player has joined)
  return (
    <main className="min-h-dvh bg-gradient-to-br from-gray-100 via-gray-100 to-gray-200 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950 px-4 py-8">
      <div className="mx-auto max-w-md space-y-6">
        {/* Game Code */}
        {game && (
          <Card>
            <GameCodeDisplay code={game.code} />
          </Card>
        )}

        {/* Players */}
        {game && (
          <Card>
            <PlayerList
              players={game.players}
              hostId={game.host_id}
              currentPlayerId={playerInfo.id}
            />
          </Card>
        )}

        {/* Rooms */}
        {game && (
          <Card>
            <RoomList
              rooms={game.rooms}
              gameCode={gameCode}
              token={token}
              onMutate={refetch}
            />
          </Card>
        )}

        {/* Weapons */}
        {game && (
          <Card>
            <WeaponList
              weapons={game.weapons}
              gameCode={gameCode}
              token={token}
              onMutate={refetch}
            />
          </Card>
        )}

        {/* Start Game (host only) */}
        {isHost && (
          <Card>
            <div className="space-y-3">
              <Button
                onClick={handleStartGame}
                loading={isStarting}
                disabled={!canStart}
                className="w-full"
              >
                Start Game
              </Button>
              {!canStart && startDisabledReason && (
                <p className="text-sm text-gray-500 dark:text-gray-400 text-center">
                  {startDisabledReason.charAt(0).toUpperCase() +
                    startDisabledReason.slice(1)}
                </p>
              )}
              {startError && (
                <p className="text-sm text-red-500 dark:text-red-400 text-center" role="alert">
                  {startError}
                </p>
              )}
            </div>
          </Card>
        )}

        {/* Non-host waiting message */}
        {!isHost && game && (
          <div className="text-center py-4">
            <p className="text-sm text-gray-400 dark:text-gray-500">
              Waiting for the host to start the game...
            </p>
          </div>
        )}
      </div>
    </main>
  );
}
