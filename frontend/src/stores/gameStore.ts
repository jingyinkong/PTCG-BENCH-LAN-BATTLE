import { create } from 'zustand';
import { GameState, Action, ChooseCardPrompt, LogEntry } from '../types/game';
import { api, getWsBase } from '../services/api';
import axios from 'axios';
import { preloadCardImagesByName, preloadCardImagesForState } from '../services/cardImagePreloader';

let cardImagesLoadPromise: Promise<void> | null = null;

function preloadGameImages(data: {
  state?: GameState | null;
  chooseCardPrompt?: ChooseCardPrompt | null;
}) {
  const { cardImages } = useGameStore.getState();
  preloadCardImagesForState(data.state, cardImages);
  preloadCardImagesByName(data.chooseCardPrompt?.candidates ?? [], cardImages);
}

interface GameStore {
  gameId: string | null;
  state: GameState | null;
  availableActions: Action[];
  turn: 'player1' | 'player2' | null;
  done: boolean;
  winner: 'player1' | 'player2' | null;
  loading: boolean;
  error: string | null;
  cardImages: Record<string, string>;
  imagesLoaded: boolean;
  isChoosingCard: boolean;
  chooseCardPrompt: ChooseCardPrompt | null;
  gameLog: LogEntry[];

  // Agent mode
  vsAgent: boolean;
  agentPlayer: 'player1' | 'player2';
  agentType: string | null;
  agentModel: string | null;
  isAgentThinking: boolean;

  // PvP mode
  isPvP: boolean;
  pvpPlayerId: 'player1' | 'player2' | null;
  pvpSocket: WebSocket | null;
  opponentDisconnected: boolean;
  reconnectCountdown: number;
  opponentLeft: boolean;
  coinTossResult: {
    phase: string;
    caller?: string;
    caller_name?: string;
    caller_choice?: string;
    coin?: string;
    chooser?: string;
    chooser_name?: string;
  } | null;
  sendCoinTossCall: (choice: string) => void;
  sendCoinTossChoose: (choice: string) => void;

  createGame: (config: { deck1?: string; deck2?: string; seed: number; agent?: string; agentPlayer?: string; agentModel?: string }) => Promise<void>;
  executeAction: (actionIndex: number) => Promise<void>;
  agentStep: () => Promise<void>;
  reset: () => void;
  loadCardImages: () => Promise<void>;
  getCardImageUrl: (cardName: string) => string | undefined;
  startPvPGame: (roomId: string, playerId: 'player1' | 'player2') => void;
  leavePvPGame: () => void;
}

export const useGameStore = create<GameStore>((set, get) => ({
  gameId: null,
  state: null,
  availableActions: [],
  turn: null,
  done: false,
  winner: null,
  loading: false,
  error: null,
  cardImages: {},
  imagesLoaded: false,
  isChoosingCard: false,
  chooseCardPrompt: null,
  gameLog: [],

  vsAgent: false,
  agentPlayer: 'player2',
  agentType: null,
  agentModel: null,
  isAgentThinking: false,

  isPvP: false,
  pvpPlayerId: null,
  pvpSocket: null,
  opponentDisconnected: false,
  reconnectCountdown: 0,
  opponentLeft: false,
  coinTossResult: null,

  createGame: async (config) => {
    set({ loading: true, error: null });
    try {
      const imagesPromise = get().imagesLoaded ? Promise.resolve() : get().loadCardImages();
      const data = await api.createGame(config);
      await imagesPromise;
      const newTurn = data.turn?.toLowerCase() as 'player1' | 'player2' | null;
      const agentPlayer = (data.agentPlayer?.toLowerCase() ?? config.agentPlayer ?? 'player2') as 'player1' | 'player2';
      const vsAgent = data.vsAgent ?? false;

      set({
        gameId: data.gameId,
        state: data.state,
        availableActions: data.availableActions,
        turn: newTurn,
        done: data.done,
        winner: data.winner,
        loading: false,
        isChoosingCard: data.isChoosingCard ?? false,
        chooseCardPrompt: data.chooseCardPrompt ?? null,
        vsAgent,
        agentPlayer,
        agentType: data.agentType ?? null,
        agentModel: data.agentModel ?? null,
        isAgentThinking: false,
      });
      preloadGameImages(data);

      // If agent goes first, trigger agent steps immediately
      if (vsAgent && !data.done && newTurn === agentPlayer) {
        get().agentStep();
      }
    } catch (error) {
      set({ error: 'Failed to create game', loading: false });
      console.error(error);
    }
  },

  executeAction: async (actionIndex) => {
    const { gameId, availableActions, turn, gameLog, state, isPvP, pvpSocket } = get();
    if (!gameId) return;

    const action = availableActions[actionIndex];

    // PvP mode: send action via WebSocket — state updates arrive via socket.onmessage
    if (isPvP) {
      if (!pvpSocket || pvpSocket.readyState !== WebSocket.OPEN) {
        set({ error: 'WebSocket not connected', loading: false });
        return;
      }
      const newEntry: LogEntry = {
        id: gameLog.length,
        timestep: state?.timestep ?? 0,
        turn_number: state?.turn_number ?? 0,
        player: (turn?.toLowerCase() ?? 'player1') as 'player1' | 'player2',
        actionType: action?.actionType ?? 'Unknown',
        source: action?.source,
        target: action?.target,
        attack: action?.attack,
        ability: action?.ability,
        position: action?.position,
        chosen: action?.chosen,
      };
      set({ gameLog: [...gameLog, newEntry], loading: true, error: null });
      pvpSocket.send(JSON.stringify({ type: 'ACTION', action_index: actionIndex }));
      return;
    }

    // Single-player/AI mode: use REST API
    set({ loading: true, error: null });
    try {
      const data = await api.executeAction(gameId, actionIndex);
      const newTurn = data.turn?.toLowerCase() as 'player1' | 'player2' | null;

      const newEntry: LogEntry = {
        id: gameLog.length,
        timestep: state?.timestep ?? 0,
        turn_number: state?.turn_number ?? 0,
        player: (turn?.toLowerCase() ?? 'player1') as 'player1' | 'player2',
        actionType: action?.actionType ?? 'Unknown',
        source: action?.source,
        target: action?.target,
        attack: action?.attack,
        ability: action?.ability,
        position: action?.position,
        chosen: action?.chosen,
      };

      set({
        state: data.state,
        availableActions: data.availableActions,
        turn: newTurn,
        done: data.done,
        winner: data.winner,
        loading: false,
        isChoosingCard: data.isChoosingCard ?? false,
        chooseCardPrompt: data.chooseCardPrompt ?? null,
        gameLog: [...gameLog, newEntry],
      });
      preloadGameImages(data);

      const { vsAgent, agentPlayer } = get();
      if (vsAgent && !data.done && newTurn === agentPlayer) {
        get().agentStep();
      }
    } catch (error) {
      set({ error: 'Failed to execute action', loading: false });
      console.error(error);
    }
  },

  agentStep: async () => {
    const { gameId, vsAgent, agentPlayer } = get();
    if (!gameId || !vsAgent) return;

    set({ isAgentThinking: true });
    try {
      // Loop until it's no longer the agent's turn or game is over
      let keepGoing = true;
      while (keepGoing) {
        const data = await api.agentStep(gameId);
        const newTurn = data.turn?.toLowerCase() as 'player1' | 'player2' | null;

        // Build log entry for agent's action
        const { gameLog, state } = get();
        const takenAction = data.actionTaken;
        const newEntry: LogEntry = {
          id: gameLog.length,
          timestep: state?.timestep ?? 0,
          turn_number: state?.turn_number ?? 0,
          player: agentPlayer,
          actionType: takenAction?.actionType ?? 'Unknown',
          source: takenAction?.source,
          target: takenAction?.target,
          attack: takenAction?.attack,
          ability: takenAction?.ability,
          position: takenAction?.position,
          chosen: takenAction?.chosen,
        };

        set({
          state: data.state,
          availableActions: data.availableActions,
          turn: newTurn,
          done: data.done,
          winner: data.winner ?? null,
          isChoosingCard: data.isChoosingCard ?? false,
          chooseCardPrompt: data.chooseCardPrompt ?? null,
          gameLog: [...get().gameLog, newEntry],
        });
        preloadGameImages(data);

        keepGoing = !data.done && newTurn === agentPlayer;
      }
    } catch (error) {
      set({ error: 'Agent failed to take action' });
      console.error(error);
    } finally {
      set({ isAgentThinking: false });
    }
  },

  reset: () => {
    set({
      gameId: null,
      state: null,
      availableActions: [],
      turn: null,
      done: false,
      winner: null,
      loading: false,
      error: null,
      cardImages: get().cardImages, // Keep loaded images
      imagesLoaded: get().imagesLoaded,
      isChoosingCard: false,
      chooseCardPrompt: null,
      gameLog: [],
      vsAgent: false,
      isPvP: false,
      pvpPlayerId: null,
      pvpSocket: null,
      opponentDisconnected: false,
      reconnectCountdown: 0,
      opponentLeft: false,
      coinTossResult: null,
      agentPlayer: 'player2',
      agentType: null,
      agentModel: null,
      isAgentThinking: false,
    });
  },

  startPvPGame: (roomId, playerId) => {
    // Disconnect any existing PvP socket
    const prev = get().pvpSocket;
    if (prev) { prev.close(); }

    const wsBase = getWsBase();
    const wsUrl = wsBase
      ? `${wsBase}/ws/room/${roomId}?token=${sessionStorage.getItem('ptcg_token')}`
      : `/ws/room/${roomId}?token=${sessionStorage.getItem('ptcg_token')}`;

    const socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      set({
        isPvP: true,
        pvpPlayerId: playerId,
        pvpSocket: socket,
        opponentDisconnected: false,
        reconnectCountdown: 0,
        loading: true, // show spinner until first STATE_UPDATE
      });
      // Don't set gameId here — wait for STATE_UPDATE so App only navigates
      // to game screen when the game is actually ready (both players connected).
    };

    socket.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === 'STATE_UPDATE') {
          const newTurn = msg.turn?.toLowerCase() as 'player1' | 'player2' | null;
          // Set gameId on first STATE_UPDATE to trigger App navigation
          if (!get().gameId) {
            set({ gameId: roomId });
          }
          set({
            state: msg.state,
            availableActions: msg.availableActions || [],
            turn: newTurn,
            done: msg.done || false,
            winner: msg.winner || null,
            loading: false,
            isChoosingCard: msg.isChoosingCard ?? false,
            chooseCardPrompt: msg.chooseCardPrompt ?? null,
          });
          preloadGameImages(msg);
        } else if (msg.type === 'GAME_OVER') {
          set({
            done: true,
            winner: msg.winner?.toLowerCase() || null,
            loading: false,
          });
        } else if (msg.type === 'COIN_TOSS') {
          set({ coinTossResult: msg });
        } else if (msg.type === 'ROLE_ASSIGN') {
          set({ pvpPlayerId: msg.player });
        } else if (msg.type === 'OPPONENT_DISCONNECTED') {
          set({ opponentDisconnected: true, reconnectCountdown: 30 });
          const timer = setInterval(() => {
            const cnt = get().reconnectCountdown;
            if (cnt <= 1) {
              clearInterval(timer);
              set({ done: true, reconnectCountdown: 0 });
            } else {
              set({ reconnectCountdown: cnt - 1 });
            }
          }, 1000);
        } else if (msg.type === 'OPPONENT_LEFT') {
          set({ opponentLeft: true, loading: false });
        } else if (msg.type === 'ERROR') {
          console.error('PvP WS error:', msg.message);
          set({ loading: false });
        }
      } catch {}
    };

    socket.onclose = () => {
      set({ pvpSocket: null });
    };

    set({ pvpSocket: socket });
  },

  sendCoinTossCall: (choice: string) => {
    const socket = get().pvpSocket;
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type: "COIN_TOSS_CALL", choice }));
    }
  },

  sendCoinTossChoose: (choice: string) => {
    const socket = get().pvpSocket;
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type: "COIN_TOSS_CHOOSE", choice }));
    }
  },

  leavePvPGame: () => {
    const socket = get().pvpSocket;
    if (socket) { socket.close(); }
    get().reset();
  },

  loadCardImages: async () => {
    if (get().imagesLoaded) return;
    if (cardImagesLoadPromise) return cardImagesLoadPromise;

    cardImagesLoadPromise = (async () => {
      try {
        const response = await axios.get('/api/cards/images');
        set({ cardImages: response.data, imagesLoaded: true });
        preloadCardImagesForState(get().state, response.data);
        console.log(`Loaded ${Object.keys(response.data).length} card images`);
      } catch (error) {
        console.error('Failed to load card images:', error);
        set({ imagesLoaded: false });
      } finally {
        cardImagesLoadPromise = null;
      }
    })();

    return cardImagesLoadPromise;
  },

  getCardImageUrl: (cardName: string) => {
    const { cardImages } = get();
    return cardImages[cardName];
  },
}));
