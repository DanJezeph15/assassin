import type { GameStatus } from "../types/game";

export const statusConfig: Record<GameStatus, { label: string; classes: string }> = {
  lobby: {
    label: "Lobby",
    classes:
      "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300",
  },
  in_progress: {
    label: "In Progress",
    classes:
      "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300",
  },
  finished: {
    label: "Finished",
    classes:
      "bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300",
  },
};
