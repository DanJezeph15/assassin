import { useCallback, useEffect, useRef, useState } from "react";

interface GameCodeDisplayProps {
  code: string;
}

export default function GameCodeDisplay({ code }: GameCodeDisplayProps) {
  const [copied, setCopied] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      if (timerRef.current) clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback for browsers without clipboard API
      const textArea = document.createElement("textarea");
      textArea.value = code;
      textArea.style.position = "fixed";
      textArea.style.opacity = "0";
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand("copy");
      document.body.removeChild(textArea);
      setCopied(true);
      if (timerRef.current) clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => setCopied(false), 2000);
    }
  }, [code]);

  return (
    <div className="text-center space-y-2">
      <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Game Code</p>
      <div className="flex items-center justify-center gap-3">
        <span
          className="text-4xl font-bold font-mono tracking-[0.3em] text-gray-900 dark:text-white select-all"
          aria-label={`Game code: ${code.split("").join(" ")}`}
        >
          {code}
        </span>
        <button
          onClick={handleCopy}
          className={
            "inline-flex items-center justify-center w-10 h-10 rounded-xl " +
            "transition-all duration-200 ease-out " +
            "focus:outline-none focus:ring-2 focus:ring-red-300 dark:focus:ring-red-500/50 focus:ring-offset-2 dark:focus:ring-offset-gray-800 " +
            (copied
              ? "bg-emerald-100 dark:bg-emerald-900/40 text-emerald-600 dark:text-emerald-400"
              : "bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 " +
                "hover:bg-gray-200 dark:hover:bg-gray-600 hover:text-gray-700 dark:hover:text-gray-200 active:scale-[0.95]")
          }
          aria-label={copied ? "Copied!" : "Copy game code"}
        >
          {copied ? (
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 20 20"
              fill="currentColor"
              className="w-5 h-5"
              aria-hidden="true"
            >
              <path
                fillRule="evenodd"
                d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z"
                clipRule="evenodd"
              />
            </svg>
          ) : (
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 20 20"
              fill="currentColor"
              className="w-5 h-5"
              aria-hidden="true"
            >
              <path d="M7 3.5A1.5 1.5 0 018.5 2h3.879a1.5 1.5 0 011.06.44l3.122 3.12A1.5 1.5 0 0117 6.622V12.5a1.5 1.5 0 01-1.5 1.5h-1v-3.379a3 3 0 00-.879-2.121L10.5 5.379A3 3 0 008.379 4.5H7v-1z" />
              <path d="M4.5 6A1.5 1.5 0 003 7.5v9A1.5 1.5 0 004.5 18h7a1.5 1.5 0 001.5-1.5v-5.879a1.5 1.5 0 00-.44-1.06L9.44 6.439A1.5 1.5 0 008.378 6H4.5z" />
            </svg>
          )}
        </button>
      </div>
      <p className="text-sm text-gray-400 dark:text-gray-500">
        Share this code with your friends to join
      </p>
    </div>
  );
}
