import { useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import Input from "../components/ui/Input";
import { ApiError } from "../api/client";
import { createGame, joinGame } from "../api/endpoints";
import { savePlayerInfo, savePlayerToken } from "../utils/storage";
import { useAuth } from "../context/AuthContext";
import ActiveGamesList from "../components/ActiveGamesList";

export default function HomePage() {
  const navigate = useNavigate();
  const { authToken, openAuthModal } = useAuth();

  // Create game state
  const [isCreating, setIsCreating] = useState(false);
  const [createError, setCreateError] = useState("");

  // Join game state
  const [gameCode, setGameCode] = useState("");
  const [playerName, setPlayerName] = useState("");
  const [isJoining, setIsJoining] = useState(false);
  const [joinError, setJoinError] = useState("");
  const [codeError, setCodeError] = useState("");
  const [nameError, setNameError] = useState("");

  async function handleCreateGame() {
    if (!authToken) {
      openAuthModal();
      return;
    }
    setCreateError("");
    setIsCreating(true);
    try {
      const game = await createGame();
      navigate(`/game/${game.code}`);
    } catch (err) {
      if (err instanceof ApiError) {
        setCreateError(err.detail);
      } else {
        setCreateError("Failed to create game. Please try again.");
      }
    } finally {
      setIsCreating(false);
    }
  }

  async function handleJoinGame(e: FormEvent) {
    e.preventDefault();

    if (!authToken) {
      openAuthModal();
      return;
    }

    // Client-side validation
    setCodeError("");
    setNameError("");
    setJoinError("");

    const trimmedCode = gameCode.trim().toUpperCase();
    const trimmedName = playerName.trim();
    let hasError = false;

    if (!trimmedCode) {
      setCodeError("Enter a game code");
      hasError = true;
    } else if (trimmedCode.length !== 6) {
      setCodeError("Game code must be 6 characters");
      hasError = true;
    }

    if (!trimmedName) {
      setNameError("Enter your name");
      hasError = true;
    } else if (trimmedName.length > 50) {
      setNameError("Name must be 50 characters or less");
      hasError = true;
    }

    if (hasError) return;

    setIsJoining(true);
    try {
      const result = await joinGame(trimmedCode, trimmedName, authToken);
      savePlayerToken(trimmedCode, result.token);
      savePlayerInfo(trimmedCode, {
        id: result.id,
        name: result.name,
      });
      navigate(`/game/${trimmedCode}`);
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 404) {
          setCodeError("Game not found. Check your code and try again.");
        } else if (err.detail.toLowerCase().includes("name")) {
          setNameError(err.detail);
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

  return (
    <main className="flex min-h-dvh flex-col items-center justify-center bg-gradient-to-br from-gray-100 via-gray-100 to-gray-200 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950 px-4 py-8">
      <div className="w-full max-w-md space-y-6">
        {/* Branding */}
        <header className="text-center space-y-3">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-red-700 to-red-900 shadow-lg shadow-red-200/80 dark:shadow-red-900/30 mb-1">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="w-8 h-8 text-white"
              aria-hidden="true"
            >
              <circle cx="12" cy="12" r="10" />
              <circle cx="12" cy="12" r="6" />
              <circle cx="12" cy="12" r="2" />
              <line x1="12" y1="2" x2="12" y2="6" />
              <line x1="12" y1="18" x2="12" y2="22" />
              <line x1="2" y1="12" x2="6" y2="12" />
              <line x1="18" y1="12" x2="22" y2="12" />
            </svg>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white tracking-tight">
            Assassin
          </h1>
          <p className="text-gray-500 dark:text-gray-400 text-base leading-relaxed">
            The party game of stealth and strategy
          </p>
        </header>

        {/* Create Game */}
        <Card>
          <div className="space-y-4">
            <div className="text-center">
              <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">
                Start a new game
              </h2>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                Create a game and invite your friends
              </p>
            </div>
            <Button
              onClick={handleCreateGame}
              loading={isCreating}
              className="w-full"
            >
              Create Game
            </Button>
            {createError && (
              <p className="text-sm text-red-500 dark:text-red-400 text-center" role="alert">
                {createError}
              </p>
            )}
          </div>
        </Card>

        {/* Divider */}
        <div className="relative flex items-center" aria-hidden="true">
          <div className="flex-1 border-t border-gray-200 dark:border-gray-700" />
          <span className="mx-4 text-sm font-medium text-gray-400 dark:text-gray-500 select-none">
            or
          </span>
          <div className="flex-1 border-t border-gray-200 dark:border-gray-700" />
        </div>

        {/* Join Game */}
        <Card>
          <form onSubmit={handleJoinGame} className="space-y-4" noValidate>
            <div className="text-center">
              <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">
                Join a game
              </h2>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                Enter the code from your host
              </p>
            </div>

            <Input
              label="Game Code"
              placeholder="ABC123"
              value={gameCode}
              onChange={(e) => {
                setGameCode(e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, ""));
                setCodeError("");
              }}
              error={codeError}
              maxLength={6}
              autoCapitalize="characters"
              autoComplete="off"
              spellCheck={false}
              className="text-center text-lg font-mono tracking-widest uppercase"
            />

            <Input
              label="Your Name"
              placeholder="Enter your name"
              value={playerName}
              onChange={(e) => {
                setPlayerName(e.target.value);
                setNameError("");
              }}
              error={nameError}
              maxLength={50}
              autoComplete="off"
            />

            <Button
              type="submit"
              variant="secondary"
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

        {/* Your Games */}
        <ActiveGamesList />
      </div>
    </main>
  );
}
