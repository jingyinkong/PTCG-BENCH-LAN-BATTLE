import axios from 'axios';
import { AgentRating, DeckInfo } from '../types/game';

export interface AgentModelInfo {
  id: string;
  name: string;
  provider: string;
}

export interface AgentInfo {
  id: string;
  name: string;
  description: string;
  requiresModel: boolean;
  available: boolean;
  unavailableReason?: string;
  models?: AgentModelInfo[];
  defaultModel?: string;
}

export interface RoomInfo {
  id: string;
  host_user_id: number;
  host_username: string;
  guest_user_id: number | null;
  guest_username: string | null;
  status: 'waiting' | 'playing' | 'finished';
  host_deck: string | null;
  guest_deck: string | null;
  game_id: string | null;
  created_at: string;
  is_own?: boolean;
}

export interface MatchRecord {
  id: number;
  game_room_id: string;
  player1_name: string;
  player2_name: string;
  winner_name: string | null;
  deck1_name: string | null;
  deck2_name: string | null;
  total_turns: number;
  duration_seconds: number;
  played_at: string;
}

export interface MatchStats {
  total_games: number;
  wins: number;
  losses: number;
  win_rate: number;
  favorite_decks: { deck: string; cnt: number }[];
}

export interface ServerInfo {
  host: string;
  port: number;
  name: string;
}

const API_BASE = (import.meta as any).env?.VITE_API_BASE || '/api';

/** Derive WebSocket base URL from API_BASE for cross-machine LAN dev */
export function getWsBase(): string {
  if (API_BASE === '/api') return ''; // use relative path -> Vite proxy
  try {
    const url = new URL(API_BASE);
    url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
    url.pathname = '';
    return url.toString().replace(/\/+$/, '');
  } catch {
    return '';
  }
}

// Axios instance with auth interceptor
const client = axios.create({ baseURL: API_BASE });

client.interceptors.request.use((config) => {
  const token = sessionStorage.getItem('ptcg_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const api = {
  // ── Auth ──
  async register(username: string, password: string) {
    const res = await client.post('/auth/register', { username, password });
    return res.data;
  },
  async login(username: string, password: string) {
    const res = await client.post('/auth/login', { username, password });
    return res.data;
  },
  async logout() {
    const res = await client.post('/auth/logout');
    return res.data;
  },
  async me() {
    const res = await client.get('/auth/me');
    return res.data;
  },

  // ── LAN ──
  async serverInfo(): Promise<ServerInfo> {
    const res = await axios.get(`${API_BASE}/lan/server-info`);
    return res.data;
  },

  // ── Rooms ──
  async createRoom(deckId: string) {
    const res = await client.post('/rooms', { deck_id: deckId });
    return res.data;
  },
  async listRooms(): Promise<{ rooms: RoomInfo[] }> {
    const res = await client.get('/rooms');
    return res.data;
  },
  async joinRoom(roomId: string, deckId: string) {
    const res = await client.post(`/rooms/${roomId}/join`, { deck_id: deckId });
    return res.data;
  },
  async startRoom(roomId: string) {
    const res = await client.post(`/rooms/${roomId}/start`);
    return res.data;
  },
  async getRoom(roomId: string): Promise<{ room: RoomInfo }> {
    const res = await client.get(`/rooms/${roomId}`);
    return res.data;
  },
  async leaveRoom(roomId: string) {
    const res = await client.delete(`/rooms/${roomId}`);
    return res.data;
  },

  // ── Match Records ──
  async getMatchRecords(limit = 20, offset = 0): Promise<{ records: MatchRecord[] }> {
    const res = await client.get('/match-records', { params: { limit, offset } });
    return res.data;
  },
  async getMatchStats(): Promise<MatchStats> {
    const res = await client.get('/match-records/stats');
    return res.data;
  },

  // ── Game (existing) ──
  async createGame(config: { deck1?: string; deck2?: string; seed: number; agent?: string; agentPlayer?: string; agentModel?: string }) {
    const response = await axios.post(`${API_BASE}/game/create`, {
      deck1: config.deck1,
      deck2: config.deck2,
      seed: config.seed,
      agent: config.agent,
      agent_player: config.agentPlayer,
      agent_model: config.agentModel,
    });
    return response.data;
  },

  async listAgents() {
    const response = await axios.get(`${API_BASE}/agents`);
    return response.data as AgentInfo[];
  },

  async getGameState(gameId: string) {
    const response = await axios.get(`${API_BASE}/game/${gameId}/state`);
    return response.data;
  },

  async executeAction(gameId: string, actionIndex: number) {
    const response = await axios.post(`${API_BASE}/game/${gameId}/action`, {
      action_index: actionIndex,
    });
    return response.data;
  },

  async agentStep(gameId: string) {
    const response = await axios.post(`${API_BASE}/game/${gameId}/agent-step`);
    return response.data;
  },

  async deleteGame(gameId: string) {
    const response = await axios.delete(`${API_BASE}/game/${gameId}`);
    return response.data;
  },

  async listDecks(): Promise<DeckInfo[]> {
    const response = await axios.get(`${API_BASE}/decks`);
    return response.data;
  },

  async getLeaderboard(): Promise<AgentRating[]> {
    const response = await axios.get(`${API_BASE}/leaderboard`);
    return response.data.agents as AgentRating[];
  },

  async listReplays() {
    const response = await axios.get(`${API_BASE}/replays`);
    return response.data;
  },

  async getReplay(filename: string) {
    const response = await axios.get(`${API_BASE}/replays/${encodeURIComponent(filename)}`);
    return response.data;
  },
};
