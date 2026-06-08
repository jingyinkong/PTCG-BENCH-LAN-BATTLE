import { create } from 'zustand';
import { DeckInfo } from '../types/game';
import { api } from '../services/api';

interface DeckStore {
  decks: DeckInfo[];
  loading: boolean;
  loadDecks: () => Promise<void>;
}

export const useDeckStore = create<DeckStore>((set, get) => ({
  decks: [],
  loading: false,

  loadDecks: async () => {
    if (get().decks.length > 0) return; // already loaded
    set({ loading: true });
    try {
      const raw: any = await api.listDecks();
      // Handle both response formats: raw array or {decks: [...]}
      const decks: DeckInfo[] = Array.isArray(raw) ? raw : (raw?.decks || []);
      set({ decks, loading: false });
    } catch (err) {
      console.error('Failed to load decks:', err);
      set({ loading: false });
    }
  },
}));
