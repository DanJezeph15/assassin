import type { HTMLAttributes, ReactNode } from "react";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
}

export default function Card({ children, className = "", ...rest }: CardProps) {
  return (
    <div
      className={
        "rounded-2xl bg-white dark:bg-gray-900 shadow-lg shadow-gray-200/60 dark:shadow-black/20 p-6 sm:p-8" +
        (className ? ` ${className}` : "")
      }
      {...rest}
    >
      {children}
    </div>
  );
}
