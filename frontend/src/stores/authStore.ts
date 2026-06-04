import { create } from 'zustand';
import { api } from '../services/api';

interface AuthState {
  user: { id: number; username: string; created_at: string } | null;
  token: string | null;
  isLoggedIn: boolean;
  isLoading: boolean;
  error: string | null;
  login: (username: string, password: string) => Promise<boolean>;
  register: (username: string, password: string) => Promise<boolean>;
  logout: () => Promise<void>;
  fetchMe: () => Promise<boolean>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: sessionStorage.getItem('ptcg_token'),
  isLoggedIn: false,
  isLoading: false,
  error: null,

  login: async (username, password) => {
    set({ isLoading: true, error: null });
    try {
      const data = await api.login(username, password);
      sessionStorage.setItem('ptcg_token', data.token);
      set({ token: data.token, user: { id: data.id ?? 0, username: data.username, created_at: '' }, isLoggedIn: true, isLoading: false });
      return true;
    } catch (e: any) {
      const msg = e?.response?.data?.detail || '登录失败';
      set({ error: msg, isLoading: false });
      return false;
    }
  },

  register: async (username, password) => {
    set({ isLoading: true, error: null });
    try {
      await api.register(username, password);
      set({ isLoading: false });
      return true;
    } catch (e: any) {
      const msg = e?.response?.data?.detail || '注册失败';
      set({ error: msg, isLoading: false });
      return false;
    }
  },

  logout: async () => {
    try { await api.logout(); } catch {}
    sessionStorage.removeItem('ptcg_token');
    set({ user: null, token: null, isLoggedIn: false, error: null });
  },

  fetchMe: async () => {
    const { token } = get();
    if (!token) return false;
    try {
      const data = await api.me();
      set({ user: data, isLoggedIn: true });
      return true;
    } catch {
      sessionStorage.removeItem('ptcg_token');
      set({ token: null, isLoggedIn: false });
      return false;
    }
  },

  clearError: () => set({ error: null }),
}));
