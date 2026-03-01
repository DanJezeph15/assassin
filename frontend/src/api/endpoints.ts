// Typed API endpoint functions

import type {
  Assignment,
  CreateGameResponse,
  DeathResponse,
  Game,
  JoinGameResponse,
  LeaderboardEntry,
  Room,
  Weapon,
} from "../types/game";
import { apiClient } from "./client";

export async function createGame(): Promise<CreateGameResponse> {
  return apiClient<CreateGameResponse>("/games", {
    method: "POST",
    body: {},
  });
}

export async function joinGame(
  code: string,
  name: string,
): Promise<JoinGameResponse> {
  return apiClient<JoinGameResponse>(`/games/${code}/players`, {
    method: "POST",
    body: { name },
  });
}

export async function getGame(code: string): Promise<Game> {
  return apiClient<Game>(`/games/${code}`);
}

// Rooms

export async function addRoom(
  code: string,
  name: string,
  token: string,
): Promise<Room> {
  return apiClient<Room>(`/games/${code}/rooms`, {
    method: "POST",
    body: { name },
    token,
  });
}

export async function removeRoom(
  code: string,
  roomId: string,
  token: string,
): Promise<void> {
  return apiClient<void>(`/games/${code}/rooms/${roomId}`, {
    method: "DELETE",
    token,
  });
}

// Weapons

export async function addWeapon(
  code: string,
  name: string,
  token: string,
): Promise<Weapon> {
  return apiClient<Weapon>(`/games/${code}/weapons`, {
    method: "POST",
    body: { name },
    token,
  });
}

export async function removeWeapon(
  code: string,
  weaponId: string,
  token: string,
): Promise<void> {
  return apiClient<void>(`/games/${code}/weapons/${weaponId}`, {
    method: "DELETE",
    token,
  });
}

// Game Actions

export async function startGame(
  code: string,
  token: string,
): Promise<void> {
  return apiClient<void>(`/games/${code}/start`, {
    method: "POST",
    token,
  });
}

// Assignments

export async function getAssignment(
  code: string,
  token: string,
): Promise<Assignment> {
  return apiClient<Assignment>(`/games/${code}/assignment`, {
    token,
  });
}

// Deaths

export async function confirmDeath(
  code: string,
  token: string,
): Promise<DeathResponse> {
  return apiClient<DeathResponse>(`/games/${code}/deaths`, {
    method: "POST",
    token,
  });
}

// Leaderboard

export async function getLeaderboard(
  code: string,
  token: string,
): Promise<LeaderboardEntry[]> {
  return apiClient<LeaderboardEntry[]>(`/games/${code}/leaderboard`, {
    token,
  });
}
