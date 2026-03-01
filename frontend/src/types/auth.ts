// Auth-related TypeScript types

export interface User {
  id: string;
  username: string;
  created_at: string;
}

export interface AuthResponse {
  token: string;
  user: User;
}

export interface UserGameInfo {
  game_id: string;
  game_code: string;
  game_status: string;
  player_name: string;
  player_id: string;
}

export interface SessionRestoreResponse {
  token: string;
  player_id: string;
  player_name: string;
}

export interface LinkSessionsResponse {
  linked_count: number;
}
