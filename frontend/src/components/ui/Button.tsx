import type { ButtonHTMLAttributes, ReactNode, Ref } from "react";
import Spinner from "./Spinner";

type ButtonVariant = "primary" | "secondary" | "danger";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  loading?: boolean;
  children: ReactNode;
  ref?: Ref<HTMLButtonElement>;
}

const baseClasses =
  "inline-flex items-center justify-center font-semibold rounded-xl " +
  "min-h-[3rem] px-6 py-3 text-base transition-all duration-200 ease-out " +
  "focus:outline-none focus:ring-2 focus:ring-offset-2 dark:focus:ring-offset-gray-900 " +
  "disabled:opacity-50 disabled:cursor-not-allowed " +
  "active:scale-[0.97]";

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    "bg-gradient-to-br from-red-700 to-red-900 text-white shadow-md " +
    "shadow-red-200 dark:shadow-red-900/30 hover:from-red-800 hover:to-red-950 " +
    "focus:ring-red-400",
  secondary:
    "bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-200 " +
    "border border-gray-200 dark:border-gray-700 shadow-sm " +
    "hover:bg-gray-50 dark:hover:bg-gray-700 hover:border-gray-300 dark:hover:border-gray-600 " +
    "focus:ring-gray-300 dark:focus:ring-gray-600",
  danger:
    "bg-gradient-to-br from-red-500 to-rose-600 text-white shadow-md " +
    "shadow-rose-200 dark:shadow-rose-900/30 hover:from-red-600 hover:to-rose-700 " +
    "focus:ring-rose-400",
};

export default function Button({
  variant = "primary",
  loading = false,
  disabled,
  children,
  className = "",
  ref,
  ...rest
}: ButtonProps) {
  return (
    <button
      ref={ref}
      className={`${baseClasses} ${variantClasses[variant]} ${className}`}
      disabled={disabled || loading}
      {...rest}
    >
      {loading && <Spinner className="-ml-1 mr-2 h-5 w-5" />}
      {children}
    </button>
  );
}
