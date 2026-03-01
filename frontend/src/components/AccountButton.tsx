// Account button: sign-in trigger when logged out, avatar+dropdown when logged in

import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function AccountButton() {
  const { user, isLoading, logout, openAuthModal } = useAuth();
  const navigate = useNavigate();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    if (!dropdownOpen) return;
    function handleClick(e: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(e.target as Node)
      ) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [dropdownOpen]);

  // Close dropdown on Escape
  useEffect(() => {
    if (!dropdownOpen) return;
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") setDropdownOpen(false);
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [dropdownOpen]);

  const handleLogout = useCallback(() => {
    setDropdownOpen(false);
    logout();
  }, [logout]);

  // Don't render anything while validating stored token
  if (isLoading) return null;

  // Logged out: show Sign In button
  if (!user) {
    return (
      <button
        type="button"
        onClick={openAuthModal}
        className="text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors duration-200 px-3 py-2 rounded-lg hover:bg-white/60 dark:hover:bg-gray-800/60"
      >
        Sign In
      </button>
    );
  }

  // Logged in: avatar + username with dropdown
  const initial = user.username.charAt(0).toUpperCase();

  return (
    <div ref={dropdownRef} className="relative">
      <button
        type="button"
        onClick={() => setDropdownOpen((prev) => !prev)}
        className="flex items-center gap-2 px-2.5 py-1.5 rounded-xl transition-colors duration-200 hover:bg-white/60 dark:hover:bg-gray-800/60"
        aria-expanded={dropdownOpen}
        aria-haspopup="true"
      >
        <span
          className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-gradient-to-br from-red-700 to-red-900 text-white text-xs font-bold shadow-sm"
          aria-hidden="true"
        >
          {initial}
        </span>
        <span className="text-sm font-medium text-gray-700 dark:text-gray-200 max-w-[100px] truncate">
          {user.username}
        </span>
      </button>

      {/* Dropdown */}
      {dropdownOpen && (
        <div className="absolute right-0 top-full mt-1.5 w-44 rounded-xl bg-white dark:bg-gray-900 shadow-lg shadow-gray-200/60 dark:shadow-black/30 border border-gray-100 dark:border-gray-800 overflow-hidden z-50">
          <div className="px-4 py-2.5 border-b border-gray-100 dark:border-gray-800">
            <p className="text-xs text-gray-400 dark:text-gray-500">
              Signed in as
            </p>
            <p className="text-sm font-medium text-gray-800 dark:text-gray-200 truncate">
              {user.username}
            </p>
          </div>
          <button
            type="button"
            onClick={() => {
              setDropdownOpen(false);
              navigate("/my-games");
            }}
            className="w-full px-4 py-2.5 text-left text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800/60 hover:text-gray-900 dark:hover:text-gray-200 transition-colors duration-150"
          >
            My Games
          </button>
          <button
            type="button"
            onClick={handleLogout}
            className="w-full px-4 py-2.5 text-left text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800/60 hover:text-gray-900 dark:hover:text-gray-200 transition-colors duration-150"
          >
            Sign Out
          </button>
        </div>
      )}
    </div>
  );
}
