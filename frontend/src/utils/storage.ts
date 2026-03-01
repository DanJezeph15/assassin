// localStorage helpers for player token and info persistence

const TOKEN_KEY_PREFIX = "assassin_token_";
const PLAYER_INFO_KEY_PREFIX = "assassin_player_";

export interface PlayerInfo {
  id: string;
  name: string;
}

export function savePlayerToken(gameCode: string, token: string): void {
  localStorage.setItem(`${TOKEN_KEY_PREFIX}${gameCode}`, token);
}

export function getPlayerToken(gameCode: string): string | null {
  return localStorage.getItem(`${TOKEN_KEY_PREFIX}${gameCode}`);
}

export function clearPlayerToken(gameCode: string): void {
  localStorage.removeItem(`${TOKEN_KEY_PREFIX}${gameCode}`);
}

export function savePlayerInfo(
  gameCode: string,
  info: PlayerInfo,
): void {
  localStorage.setItem(
    `${PLAYER_INFO_KEY_PREFIX}${gameCode}`,
    JSON.stringify(info),
  );
}

export function getPlayerInfo(gameCode: string): PlayerInfo | null {
  const raw = localStorage.getItem(
    `${PLAYER_INFO_KEY_PREFIX}${gameCode}`,
  );
  if (!raw) return null;
  try {
    return JSON.parse(raw) as PlayerInfo;
  } catch {
    return null;
  }
}

export interface GameSession {
  code: string;
  token: string;
  playerInfo: PlayerInfo | null;
}

export function getAllGameSessions(): GameSession[] {
  const sessions: GameSession[] = [];
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (!key?.startsWith(TOKEN_KEY_PREFIX)) continue;
    const code = key.slice(TOKEN_KEY_PREFIX.length);
    const token = localStorage.getItem(key);
    if (!token) continue;
    sessions.push({
      code,
      token,
      playerInfo: getPlayerInfo(code),
    });
  }
  return sessions;
}

export function removeGameSession(code: string): void {
  localStorage.removeItem(`${TOKEN_KEY_PREFIX}${code}`);
  localStorage.removeItem(`${PLAYER_INFO_KEY_PREFIX}${code}`);
}

// Auth storage helpers

const AUTH_TOKEN_KEY = "assassin_auth_token";
const AUTH_USER_KEY = "assassin_auth_user";

export function saveAuthToken(token: string): void {
  localStorage.setItem(AUTH_TOKEN_KEY, token);
}

export function getAuthToken(): string | null {
  return localStorage.getItem(AUTH_TOKEN_KEY);
}

export function clearAuth(): void {
  localStorage.removeItem(AUTH_TOKEN_KEY);
  localStorage.removeItem(AUTH_USER_KEY);
}

export function saveAuthUser(user: { id: string; username: string }): void {
  localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
}

export function getAuthUser(): { id: string; username: string } | null {
  const raw = localStorage.getItem(AUTH_USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as { id: string; username: string };
  } catch {
    return null;
  }
}
