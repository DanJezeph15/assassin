// Auth API endpoint functions

import type {
  AuthResponse,
  LinkSessionsResponse,
  PaginatedUserGames,
  SessionRestoreResponse,
  User,
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
  page: number = 1,
  perPage: number = 25,
): Promise<PaginatedUserGames> {
  return apiClient<PaginatedUserGames>(
    `/auth/me/games?page=${page}&per_page=${perPage}`,
    { authToken },
  );
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
