import { useState } from "react";
import type { FormEvent, ReactNode } from "react";
import { ApiError } from "../api/client";
import Spinner from "./ui/Spinner";
import Input from "./ui/Input";
import Button from "./ui/Button";

interface EditableItemListProps {
  items: { id: string; name: string; created_by: string | null }[];
  currentPlayerId: string;
  hostId: string;
  label: string;
  singularLabel: string;
  emptyMessage: string;
  placeholder: string;
  icon: ReactNode;
  onAdd: (name: string) => Promise<void>;
  onRemove: (id: string) => Promise<void>;
}

export default function EditableItemList({
  items,
  currentPlayerId,
  hostId,
  label,
  singularLabel,
  emptyMessage,
  placeholder,
  icon,
  onAdd,
  onRemove,
}: EditableItemListProps) {
  const [newName, setNewName] = useState("");
  const [isAdding, setIsAdding] = useState(false);
  const [error, setError] = useState("");
  const [removingId, setRemovingId] = useState<string | null>(null);

  async function handleAdd(e: FormEvent) {
    e.preventDefault();
    const trimmed = newName.trim();
    if (!trimmed) return;

    setError("");
    setIsAdding(true);
    try {
      await onAdd(trimmed);
      setNewName("");
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.detail);
      } else {
        setError(`Failed to add ${singularLabel}`);
      }
    } finally {
      setIsAdding(false);
    }
  }

  async function handleRemove(id: string) {
    setRemovingId(id);
    try {
      await onRemove(id);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.detail);
      } else {
        setError(`Failed to remove ${singularLabel}`);
      }
    } finally {
      setRemovingId(null);
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
          {label}
        </h3>
        <span className="text-sm font-medium text-gray-400 dark:text-gray-500">
          {items.length}{" "}
          {items.length === 1 ? singularLabel : `${singularLabel}s`}
        </span>
      </div>

      {items.length === 0 ? (
        <p className="text-sm text-gray-400 dark:text-gray-500 py-3 text-center">
          {emptyMessage}
        </p>
      ) : (
        <ul className="space-y-1" role="list">
          {items.map((item) => (
            <li
              key={item.id}
              className="flex items-center justify-between px-3 py-2.5 rounded-xl bg-gray-50 dark:bg-gray-700/50 transition-colors duration-150 group"
            >
              <div className="flex items-center gap-2 min-w-0">
                <span className="w-4 h-4 text-gray-400 dark:text-gray-500 flex-shrink-0">
                  {icon}
                </span>
                <span className="text-base text-gray-700 dark:text-gray-200 truncate">
                  {item.name}
                </span>
              </div>
              {(currentPlayerId === hostId || item.created_by === currentPlayerId) && (
                <button
                  onClick={() => handleRemove(item.id)}
                  disabled={removingId === item.id}
                  className={
                    "flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-lg " +
                    "text-gray-400 dark:text-gray-500 hover:text-red-500 dark:hover:text-red-400 " +
                    "hover:bg-red-50 dark:hover:bg-red-900/20 " +
                    "transition-all duration-150 " +
                    "focus:outline-none focus:ring-2 focus:ring-red-300 dark:focus:ring-red-500/40 focus:ring-offset-1 dark:focus:ring-offset-gray-800 " +
                    "disabled:opacity-50 disabled:cursor-not-allowed"
                  }
                  aria-label={`Remove ${item.name}`}
                >
                  {removingId === item.id ? (
                    <Spinner className="w-4 h-4" />
                  ) : (
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                      className="w-4 h-4"
                      aria-hidden="true"
                    >
                      <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
                    </svg>
                  )}
                </button>
              )}
            </li>
          ))}
        </ul>
      )}

      <form onSubmit={handleAdd} className="flex items-start gap-2">
        <div className="flex-1">
          <Input
            placeholder={placeholder}
            value={newName}
            onChange={(e) => {
              setNewName(e.target.value);
              setError("");
            }}
            error={error}
            maxLength={100}
            autoComplete="off"
          />
        </div>
        <Button
          type="submit"
          variant="secondary"
          loading={isAdding}
          disabled={!newName.trim()}
          className="flex-shrink-0 !px-4"
        >
          Add
        </Button>
      </form>
    </div>
  );
}
