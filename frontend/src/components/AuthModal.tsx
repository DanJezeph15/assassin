// Auth modal for Sign In / Register with tab switching

import { useCallback, useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import Button from "./ui/Button";
import Input from "./ui/Input";
import { useAuth } from "../context/AuthContext";
import { ApiError } from "../api/client";

type AuthTab = "signin" | "register";

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
}

// Validation rules matching backend
const USERNAME_MIN = 3;
const USERNAME_MAX = 30;
const USERNAME_PATTERN = /^[a-zA-Z0-9_-]+$/;
const PASSWORD_MIN = 6;

export default function AuthModal({ isOpen, onClose }: AuthModalProps) {
  const { login, register } = useAuth();
  const [activeTab, setActiveTab] = useState<AuthTab>("signin");
  const backdropRef = useRef<HTMLDivElement>(null);

  // Sign In state
  const [signInUsername, setSignInUsername] = useState("");
  const [signInPassword, setSignInPassword] = useState("");
  const [signInUsernameError, setSignInUsernameError] = useState("");
  const [signInPasswordError, setSignInPasswordError] = useState("");
  const [signInError, setSignInError] = useState("");
  const [isSigningIn, setIsSigningIn] = useState(false);

  // Register state
  const [regUsername, setRegUsername] = useState("");
  const [regPassword, setRegPassword] = useState("");
  const [regConfirm, setRegConfirm] = useState("");
  const [regUsernameError, setRegUsernameError] = useState("");
  const [regPasswordError, setRegPasswordError] = useState("");
  const [regConfirmError, setRegConfirmError] = useState("");
  const [regError, setRegError] = useState("");
  const [isRegistering, setIsRegistering] = useState(false);

  // Reset form state when modal opens/closes or tab switches
  useEffect(() => {
    if (!isOpen) return;
    setSignInUsername("");
    setSignInPassword("");
    setSignInUsernameError("");
    setSignInPasswordError("");
    setSignInError("");
    setRegUsername("");
    setRegPassword("");
    setRegConfirm("");
    setRegUsernameError("");
    setRegPasswordError("");
    setRegConfirmError("");
    setRegError("");
  }, [isOpen]);

  // Close on Escape
  useEffect(() => {
    if (!isOpen) return;
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  // Trap focus: prevent background scrolling when modal is open
  useEffect(() => {
    if (!isOpen) return;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  const handleBackdropClick = useCallback(
    (e: React.MouseEvent) => {
      if (e.target === backdropRef.current) onClose();
    },
    [onClose],
  );

  function validateUsername(username: string): string {
    const trimmed = username.trim();
    if (!trimmed) return "Username is required";
    if (trimmed.length < USERNAME_MIN)
      return `Username must be at least ${USERNAME_MIN} characters`;
    if (trimmed.length > USERNAME_MAX)
      return `Username must be ${USERNAME_MAX} characters or less`;
    if (!USERNAME_PATTERN.test(trimmed))
      return "Username can only contain letters, numbers, underscores, and hyphens";
    return "";
  }

  function validatePassword(password: string): string {
    if (!password) return "Password is required";
    if (password.length < PASSWORD_MIN)
      return `Password must be at least ${PASSWORD_MIN} characters`;
    return "";
  }

  async function handleSignIn(e: FormEvent) {
    e.preventDefault();
    setSignInUsernameError("");
    setSignInPasswordError("");
    setSignInError("");

    const trimmedUsername = signInUsername.trim();
    const usernameErr = validateUsername(trimmedUsername);
    const passwordErr = validatePassword(signInPassword);

    if (usernameErr) setSignInUsernameError(usernameErr);
    if (passwordErr) setSignInPasswordError(passwordErr);
    if (usernameErr || passwordErr) return;

    setIsSigningIn(true);
    try {
      await login(trimmedUsername, signInPassword);
      onClose();
    } catch (err) {
      if (err instanceof ApiError) {
        setSignInError(err.detail);
      } else {
        setSignInError("Sign in failed. Please try again.");
      }
    } finally {
      setIsSigningIn(false);
    }
  }

  async function handleRegister(e: FormEvent) {
    e.preventDefault();
    setRegUsernameError("");
    setRegPasswordError("");
    setRegConfirmError("");
    setRegError("");

    const trimmedUsername = regUsername.trim();
    const usernameErr = validateUsername(trimmedUsername);
    const passwordErr = validatePassword(regPassword);
    let confirmErr = "";

    if (!regConfirm) {
      confirmErr = "Please confirm your password";
    } else if (regPassword !== regConfirm) {
      confirmErr = "Passwords do not match";
    }

    if (usernameErr) setRegUsernameError(usernameErr);
    if (passwordErr) setRegPasswordError(passwordErr);
    if (confirmErr) setRegConfirmError(confirmErr);
    if (usernameErr || passwordErr || confirmErr) return;

    setIsRegistering(true);
    try {
      await register(trimmedUsername, regPassword);
      onClose();
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.detail.toLowerCase().includes("username")) {
          setRegUsernameError(err.detail);
        } else {
          setRegError(err.detail);
        }
      } else {
        setRegError("Registration failed. Please try again.");
      }
    } finally {
      setIsRegistering(false);
    }
  }

  if (!isOpen) return null;

  return (
    <div
      ref={backdropRef}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm px-4"
      onClick={handleBackdropClick}
      role="dialog"
      aria-modal="true"
      aria-label={activeTab === "signin" ? "Sign in" : "Create account"}
    >
      <div className="w-full max-w-sm rounded-2xl bg-white dark:bg-gray-900 shadow-2xl shadow-black/20 overflow-hidden animate-in">
        {/* Tab switcher */}
        <div className="flex border-b border-gray-100 dark:border-gray-800">
          <button
            type="button"
            onClick={() => setActiveTab("signin")}
            className={
              "flex-1 py-3.5 text-sm font-semibold transition-colors duration-200 " +
              (activeTab === "signin"
                ? "text-red-700 dark:text-red-400 border-b-2 border-red-700 dark:border-red-400"
                : "text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300")
            }
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("register")}
            className={
              "flex-1 py-3.5 text-sm font-semibold transition-colors duration-200 " +
              (activeTab === "register"
                ? "text-red-700 dark:text-red-400 border-b-2 border-red-700 dark:border-red-400"
                : "text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300")
            }
          >
            Register
          </button>
        </div>

        {/* Form content */}
        <div className="p-6">
          {activeTab === "signin" ? (
            <form onSubmit={handleSignIn} className="space-y-4" noValidate>
              <Input
                label="Username"
                placeholder="Enter your username"
                value={signInUsername}
                onChange={(e) => {
                  setSignInUsername(e.target.value);
                  setSignInUsernameError("");
                }}
                error={signInUsernameError}
                maxLength={USERNAME_MAX}
                autoComplete="username"
                autoFocus
              />
              <Input
                label="Password"
                type="password"
                placeholder="Enter your password"
                value={signInPassword}
                onChange={(e) => {
                  setSignInPassword(e.target.value);
                  setSignInPasswordError("");
                }}
                error={signInPasswordError}
                autoComplete="current-password"
              />
              <Button
                type="submit"
                loading={isSigningIn}
                className="w-full"
              >
                Sign In
              </Button>
              {signInError && (
                <p
                  className="text-sm text-red-500 dark:text-red-400 text-center"
                  role="alert"
                >
                  {signInError}
                </p>
              )}
            </form>
          ) : (
            <form onSubmit={handleRegister} className="space-y-4" noValidate>
              <Input
                label="Username"
                placeholder="Choose a username"
                value={regUsername}
                onChange={(e) => {
                  setRegUsername(e.target.value);
                  setRegUsernameError("");
                }}
                error={regUsernameError}
                maxLength={USERNAME_MAX}
                autoComplete="username"
                autoFocus
              />
              <Input
                label="Password"
                type="password"
                placeholder="Create a password"
                value={regPassword}
                onChange={(e) => {
                  setRegPassword(e.target.value);
                  setRegPasswordError("");
                }}
                error={regPasswordError}
                autoComplete="new-password"
              />
              <Input
                label="Confirm Password"
                type="password"
                placeholder="Confirm your password"
                value={regConfirm}
                onChange={(e) => {
                  setRegConfirm(e.target.value);
                  setRegConfirmError("");
                }}
                error={regConfirmError}
                autoComplete="new-password"
              />
              <Button
                type="submit"
                loading={isRegistering}
                className="w-full"
              >
                Create Account
              </Button>
              {regError && (
                <p
                  className="text-sm text-red-500 dark:text-red-400 text-center"
                  role="alert"
                >
                  {regError}
                </p>
              )}
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
