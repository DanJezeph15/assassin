import { useCallback, useEffect, useRef } from "react";
import Card from "./ui/Card";
import Button from "./ui/Button";
import WarningIcon from "./ui/WarningIcon";

interface DeathConfirmModalProps {
  open: boolean;
  loading: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export default function DeathConfirmModal({
  open,
  loading,
  onConfirm,
  onCancel,
}: DeathConfirmModalProps) {
  const modalRef = useRef<HTMLDivElement>(null);
  const cancelButtonRef = useRef<HTMLButtonElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);

  // Focus the cancel button when modal opens, restore focus when it closes
  useEffect(() => {
    if (open) {
      previousFocusRef.current = document.activeElement as HTMLElement;
      // Small delay to allow the modal to render before focusing
      requestAnimationFrame(() => {
        cancelButtonRef.current?.focus();
      });
    } else if (previousFocusRef.current) {
      previousFocusRef.current.focus();
      previousFocusRef.current = null;
    }
  }, [open]);

  // Prevent body scroll while modal is open
  useEffect(() => {
    if (open) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  // Handle Escape key
  useEffect(() => {
    if (!open || loading) return;

    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") {
        e.preventDefault();
        onCancel();
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open, loading, onCancel]);

  // Focus trap
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key !== "Tab" || !modalRef.current) return;

      const focusableElements = modalRef.current.querySelectorAll<HTMLElement>(
        'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
      );

      if (focusableElements.length === 0) return;

      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];

      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          e.preventDefault();
          lastElement.focus();
        }
      } else {
        if (document.activeElement === lastElement) {
          e.preventDefault();
          firstElement.focus();
        }
      }
    },
    [],
  );

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="death-confirm-title"
      ref={modalRef}
      onKeyDown={handleKeyDown}
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-gray-900/60 backdrop-blur-sm"
        onClick={loading ? undefined : onCancel}
        aria-hidden="true"
      />

      {/* Modal content */}
      <Card className="relative z-10 w-full max-w-sm">
        <div className="space-y-5">
          {/* Icon */}
          <div className="flex justify-center">
            <div className="w-14 h-14 rounded-2xl bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
              <WarningIcon className="w-7 h-7 text-red-500 dark:text-red-400" />
            </div>
          </div>

          {/* Text */}
          <div className="text-center space-y-2">
            <h2
              id="death-confirm-title"
              className="text-xl font-bold text-gray-900 dark:text-white"
            >
              Confirm your death
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400 leading-relaxed">
              Are you sure you have been killed? This action cannot be undone
              and you will be eliminated from the game.
            </p>
          </div>

          {/* Actions */}
          <div className="flex flex-col gap-2.5">
            <Button
              variant="danger"
              onClick={onConfirm}
              loading={loading}
              className="w-full"
            >
              Yes, I have been killed
            </Button>
            <Button
              ref={cancelButtonRef}
              variant="secondary"
              onClick={onCancel}
              disabled={loading}
              className="w-full"
            >
              Cancel
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
