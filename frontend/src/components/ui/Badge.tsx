type BadgeColor = "amber" | "blue" | "green" | "red";

interface BadgeProps {
  label: string;
  color: BadgeColor;
}

const colorClasses: Record<BadgeColor, string> = {
  amber: "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300",
  blue: "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300",
  green: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300",
  red: "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300",
};

export default function Badge({ label, color }: BadgeProps) {
  return (
    <span
      className={
        "inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium " +
        colorClasses[color]
      }
    >
      {label}
    </span>
  );
}
