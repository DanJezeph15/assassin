import type { Player } from "../types/game";
import Badge from "./ui/Badge";

interface PlayerListProps {
  players: Player[];
  hostId: string | null;
  currentPlayerId: string | null;
}

export default function PlayerList({
  players,
  hostId,
  currentPlayerId,
}: PlayerListProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
          Players
        </h3>
        <span className="text-sm font-medium text-gray-400 dark:text-gray-500" aria-live="polite">
          {players.length} {players.length === 1 ? "player" : "players"}
        </span>
      </div>

      {players.length === 0 ? (
        <p className="text-sm text-gray-400 dark:text-gray-500 py-3 text-center">
          No players yet. Share the code to invite friends!
        </p>
      ) : (
        <ul className="space-y-1" role="list">
          {players.map((player) => (
            <li
              key={player.id}
              className="flex items-center justify-between px-3 py-2.5 rounded-xl bg-gray-50 dark:bg-gray-700/50 transition-colors duration-150"
            >
              <div className="flex items-center gap-2 min-w-0">
                {/* Avatar circle with initial */}
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-red-600 to-red-800 flex items-center justify-center">
                  <span className="text-sm font-bold text-white leading-none">
                    {player.name.charAt(0).toUpperCase()}
                  </span>
                </div>
                <span className="text-base font-medium text-gray-800 dark:text-gray-200 truncate">
                  {player.name}
                </span>
              </div>

              <div className="flex items-center gap-1.5 flex-shrink-0">
                {player.id === hostId && <Badge label="Host" color="amber" />}
                {player.id === currentPlayerId && (
                  <Badge label="You" color="blue" />
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
