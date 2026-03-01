// TypeScript types mirroring backend Pydantic schemas

export type GameStatus = "lobby" | "in_progress" | "finished";

export interface Player {
  id: string;
  name: string;
  is_alive: boolean;
  kills: number;
}

export interface Room {
  id: string;
  name: string;
  created_by: string | null;
}

export interface Weapon {
  id: string;
  name: string;
  created_by: string | null;
}

export interface Game {
  id: string;
  code: string;
  status: GameStatus;
  host_id: string | null;
  created_at: string;
  players: Player[];
  rooms: Room[];
  weapons: Weapon[];
}

export interface Assignment {
  target_name: string;
  room_name: string;
  weapon_name: string;
}

// API response types

export interface CreateGameResponse {
  id: string;
  code: string;
  status: GameStatus;
}

export interface JoinGameResponse {
  id: string;
  name: string;
  token: string;
}

export interface LeaderboardEntry {
  name: string;
  kills: number;
  is_alive: boolean;
}

export interface DeathResponse {
  killer_name: string;
  kill_count: number;
  game_over: boolean;
  winner_name: string | null;
}
