import type { Assignment } from "../types/game";

interface AssignmentCardProps {
  assignment: Assignment;
}

export default function AssignmentCard({ assignment }: AssignmentCardProps) {
  return (
    <div
      className={
        "relative overflow-hidden rounded-2xl " +
        "bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 " +
        "p-6 sm:p-8 shadow-xl shadow-gray-900/20"
      }
    >
      {/* Subtle decorative glow */}
      <div
        className="absolute -top-24 -right-24 w-48 h-48 rounded-full bg-red-500/10 blur-3xl pointer-events-none"
        aria-hidden="true"
      />
      <div
        className="absolute -bottom-16 -left-16 w-40 h-40 rounded-full bg-rose-500/10 blur-3xl pointer-events-none"
        aria-hidden="true"
      />

      <div className="relative space-y-5">
        {/* Header */}
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-red-500/20 flex items-center justify-center flex-shrink-0">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 20 20"
              fill="currentColor"
              className="w-4 h-4 text-red-400"
              aria-hidden="true"
            >
              <path d="M10 12.5a2.5 2.5 0 100-5 2.5 2.5 0 000 5z" />
              <path
                fillRule="evenodd"
                d="M.664 10.59a1.651 1.651 0 010-1.186A10.004 10.004 0 0110 3c4.257 0 7.893 2.66 9.336 6.41.147.381.146.804 0 1.186A10.004 10.004 0 0110 17c-4.257 0-7.893-2.66-9.336-6.41zM14 10a4 4 0 11-8 0 4 4 0 018 0z"
                clipRule="evenodd"
              />
            </svg>
          </div>
          <h2 className="text-xs font-semibold uppercase tracking-wider text-gray-400">
            Your Mission
          </h2>
        </div>

        {/* Mission content */}
        <div className="space-y-4">
          {/* Target */}
          <div className="space-y-1">
            <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
              Target
            </span>
            <p className="text-2xl sm:text-3xl font-bold text-white leading-tight">
              {assignment.target_name}
            </p>
          </div>

          {/* Divider */}
          <div className="border-t border-gray-700/60" aria-hidden="true" />

          {/* Room and Weapon row */}
          <div className="grid grid-cols-2 gap-4">
            {/* Room */}
            <div className="space-y-1">
              <div className="flex items-center gap-1.5">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                  className="w-3.5 h-3.5 text-blue-400"
                  aria-hidden="true"
                >
                  <path
                    fillRule="evenodd"
                    d="M9.293 2.293a1 1 0 011.414 0l7 7A1 1 0 0117 11h-1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-3a1 1 0 00-1-1H9a1 1 0 00-1 1v3a1 1 0 01-1 1H5a1 1 0 01-1-1v-6H3a1 1 0 01-.707-1.707l7-7z"
                    clipRule="evenodd"
                  />
                </svg>
                <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                  Room
                </span>
              </div>
              <p className="text-lg font-semibold text-blue-300">
                {assignment.room_name}
              </p>
            </div>

            {/* Weapon */}
            <div className="space-y-1">
              <div className="flex items-center gap-1.5">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                  className="w-3.5 h-3.5 text-rose-400"
                  aria-hidden="true"
                >
                  <path
                    fillRule="evenodd"
                    d="M13.5 4.938a7 7 0 11-9.006 1.737c.202-.257.59-.218.793.039.278.352.594.672.943.954.332.269.786-.049.773-.476a5.977 5.977 0 01.572-2.759 6.026 6.026 0 012.486-2.665c.247-.14.55-.016.677.238A6.967 6.967 0 0013.5 4.938zM14 12a4.002 4.002 0 01-3.3 3.94c-.427.076-.774-.31-.774-.746V12.59c0-.31.2-.583.494-.694a1.997 1.997 0 00-.494-3.874c-.3 0-.585.066-.84.185-.251.116-.536-.018-.605-.289a4.003 4.003 0 014.519 4.082z"
                    clipRule="evenodd"
                  />
                </svg>
                <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                  Weapon
                </span>
              </div>
              <p className="text-lg font-semibold text-rose-300">
                {assignment.weapon_name}
              </p>
            </div>
          </div>
        </div>

        {/* Footer hint */}
        <p className="text-xs text-gray-500 text-center pt-1">
          Get your target alone in the room with the weapon
        </p>
      </div>
    </div>
  );
}
