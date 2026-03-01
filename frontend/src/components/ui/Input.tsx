import { useId } from "react";
import type { InputHTMLAttributes } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export default function Input({
  label,
  error,
  id,
  className = "",
  ...rest
}: InputProps) {
  const generatedId = useId();
  const inputId = id ?? generatedId;

  return (
    <div className="w-full">
      {label && (
        <label
          htmlFor={inputId}
          className="block text-sm font-medium text-gray-600 dark:text-gray-300 mb-1.5"
        >
          {label}
        </label>
      )}
      <input
        id={inputId}
        className={
          "w-full rounded-xl border bg-white dark:bg-gray-800 px-4 py-3 text-base " +
          "text-gray-900 dark:text-gray-100 " +
          "placeholder:text-gray-400 dark:placeholder:text-gray-500 transition-all duration-200 " +
          "focus:outline-none focus:ring-2 focus:ring-offset-1 dark:focus:ring-offset-gray-900 " +
          (error
            ? "border-red-300 dark:border-red-500/50 focus:border-red-400 focus:ring-red-300 dark:focus:ring-red-500/40"
            : "border-gray-200 dark:border-gray-700 focus:border-red-400 dark:focus:border-red-500 " +
              "focus:ring-red-300 dark:focus:ring-red-500/40 " +
              "hover:border-gray-300 dark:hover:border-gray-600") +
          (className ? ` ${className}` : "")
        }
        aria-invalid={error ? "true" : undefined}
        aria-describedby={error && inputId ? `${inputId}-error` : undefined}
        {...rest}
      />
      {error && (
        <p
          id={inputId ? `${inputId}-error` : undefined}
          className="mt-1.5 text-sm text-red-500 dark:text-red-400"
          role="alert"
        >
          {error}
        </p>
      )}
    </div>
  );
}
