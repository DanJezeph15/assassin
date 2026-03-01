// Auth API endpoint functions

import type {
  AuthResponse,
  LinkSessionsResponse,
  SessionRestoreResponse,
  User,
  UserGameInfo,
} from "../types/auth";
import { apiClient } from "./client";

export async function register(
  username: string,
  password: string,
): Promise<AuthResponse> {
  return apiClient<AuthResponse>("/auth/register", {
    method: "POST",
    body: { username, password },
  });
}

export async function login(
  username: string,
  password: string,
): Promise<AuthResponse> {
  return apiClient<AuthResponse>("/auth/login", {
    method: "POST",
    body: { username, password },
  });
}

export async function getProfile(authToken: string): Promise<User> {
  return apiClient<User>("/auth/me", { authToken });
}

export async function getUserGames(
  authToken: string,
): Promise<UserGameInfo[]> {
  return apiClient<UserGameInfo[]>("/auth/me/games", { authToken });
}

export async function restoreSession(
  authToken: string,
  code: string,
): Promise<SessionRestoreResponse> {
  return apiClient<SessionRestoreResponse>(
    `/auth/me/games/${code}/restore-session`,
    {
      method: "POST",
      authToken,
    },
  );
}

export async function linkSessions(
  authToken: string,
  tokens: string[],
): Promise<LinkSessionsResponse> {
  return apiClient<LinkSessionsResponse>("/auth/me/link-sessions", {
    method: "POST",
    body: { tokens },
    authToken,
  });
}
