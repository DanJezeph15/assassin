import type { LeaderboardEntry } from "../types/game";
import Badge from "./ui/Badge";

interface LeaderboardProps {
  entries: LeaderboardEntry[];
  currentPlayerName: string | null;
  theme?: "light" | "dark";
}

export default function Leaderboard({
  entries,
  currentPlayerName,
  theme = "light",
}: LeaderboardProps) {
  const dark = theme === "dark";

  // Sort by kills descending, then by name alphabetically for tie-breaking
  const sorted = [...entries].sort((a, b) => {
    if (b.kills !== a.kills) return b.kills - a.kills;
    return a.name.localeCompare(b.name);
  });

  return (
    <div className="space-y-3">
      <h3
        className={
          "text-sm font-semibold uppercase tracking-wider " +
          (dark
            ? "text-gray-400"
            : "text-gray-500 dark:text-gray-400")
        }
      >
        Leaderboard
      </h3>

      {sorted.length === 0 ? (
        <p
          className={
            "text-sm py-3 text-center " +
            (dark
              ? "text-gray-500"
              : "text-gray-400 dark:text-gray-500")
          }
        >
          No players to show
        </p>
      ) : (
        <ul className="space-y-1" role="list">
          {sorted.map((entry, index) => {
            const isCurrentPlayer = entry.name === currentPlayerName;
            const rank = index + 1;

            return (
              <li
                key={entry.name}
                className={
                  "flex items-center justify-between px-3 py-2.5 rounded-xl " +
                  "transition-colors duration-150 " +
                  (isCurrentPlayer
                    ? dark
                      ? "bg-red-900/20 ring-1 ring-red-700"
                      : "bg-red-50 dark:bg-red-900/20 ring-1 ring-red-200 dark:ring-red-700"
                    : dark
                      ? "bg-gray-700/50"
                      : "bg-gray-50 dark:bg-gray-700/50")
                }
              >
                <div className="flex items-center gap-2.5 min-w-0">
                  {/* Rank */}
                  <span
                    className={
                      "w-6 h-6 rounded-lg flex items-center justify-center text-xs font-bold flex-shrink-0 " +
                      (rank === 1
                        ? dark
                          ? "bg-red-900/40 text-red-300"
                          : "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300"
                        : rank === 2
                          ? dark
                            ? "bg-gray-600 text-gray-300"
                            : "bg-gray-200 text-gray-600 dark:bg-gray-600 dark:text-gray-300"
                          : rank === 3
                            ? dark
                              ? "bg-rose-900/40 text-rose-300"
                              : "bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300"
                            : dark
                              ? "bg-gray-700 text-gray-400"
                              : "bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400")
                    }
                  >
                    {rank}
                  </span>

                  {/* Name */}
                  <span
                    className={
                      "text-sm font-medium truncate " +
                      (entry.is_alive
                        ? dark
                          ? "text-gray-200"
                          : "text-gray-800 dark:text-gray-200"
                        : dark
                          ? "text-gray-500 line-through"
                          : "text-gray-400 dark:text-gray-500 line-through")
                    }
                  >
                    {entry.name}
                  </span>

                  {isCurrentPlayer && (
                    <Badge label="You" color="blue" />
                  )}
                </div>

                <div className="flex items-center gap-2 flex-shrink-0">
                  {/* Kill count */}
                  <span
                    className={
                      "text-sm font-semibold tabular-nums " +
                      (dark
                        ? "text-gray-300"
                        : "text-gray-700 dark:text-gray-300")
                    }
                  >
                    {entry.kills} {entry.kills === 1 ? "kill" : "kills"}
                  </span>

                  {/* Alive/Dead badge */}
                  <Badge
                    label={entry.is_alive ? "Alive" : "Dead"}
                    color={entry.is_alive ? "green" : "red"}
                  />
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
