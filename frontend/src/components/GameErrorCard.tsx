import Card from "./ui/Card";
import Button from "./ui/Button";
import WarningIcon from "./ui/WarningIcon";

interface GameErrorCardProps {
  errorStatus: number | null;
  errorMessage: string;
  onRetry?: () => void;
  onGoHome: () => void;
}

export default function GameErrorCard({
  errorStatus,
  errorMessage,
  onRetry,
  onGoHome,
}: GameErrorCardProps) {
  const isNotFound = errorStatus === 404;

  return (
    <Card className="max-w-md w-full text-center">
      <div className="space-y-4">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-red-100 dark:bg-red-900/30">
          <WarningIcon className="w-7 h-7 text-red-500 dark:text-red-400" />
        </div>
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">
          {isNotFound ? "Game not found" : "Could not load game"}
        </h2>
        <p className="text-gray-500 dark:text-gray-400 text-sm">
          {isNotFound
            ? "This game doesn't exist or may have been removed. Check the code and try again."
            : errorMessage}
        </p>
        <div className="flex gap-3 justify-center pt-2">
          {onRetry && !isNotFound && (
            <Button variant="secondary" onClick={onRetry}>
              Try Again
            </Button>
          )}
          <Button
            variant={onRetry && !isNotFound ? "secondary" : "primary"}
            onClick={onGoHome}
          >
            Go Home
          </Button>
        </div>
      </div>
    </Card>
  );
}
