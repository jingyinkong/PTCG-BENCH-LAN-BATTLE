// Type definitions for i18n translation namespaces

export interface CommonTranslations {
  nav: {
    home: string; game: string; decks: string; replay: string;
    leaderboard: string; history: string; lobby: string; auth: string;
    login: string; logout: string; register: string;
    vsHuman: string; vsAI: string; lanBattle: string;
    startGameFirst: string;
  };
  button: {
    confirm: string; cancel: string; back: string; close: string;
    backToHome: string; backToLobby: string; playAgain: string;
    newGame: string; startGame: string; browseDecks: string; documentation: string;
  };
  status: {
    loading: string; processing: string; yourTurn: string;
    opponentTurn: string; waiting: string; choosing: string; noActions: string;
    unavailable: string;
  };
  language: { switchTo: string };
}

export interface GameTranslations {
  zone: Record<string, string>;
  action: Record<string, string>;
  dropLabel: Record<string, string>;
  playZoneLabel: Record<string, string>;
  player: Record<string, string>;
  gameInfo: Record<string, string>;
  result: Record<string, string>;
  desc: {
    dmg: string; pos: string; ability: string; arrow: string;
  };
  reveal: string; hide: string; clickToView: string;
}

export interface LobbyTranslations {
  title: string; createRoom: string; noRooms: string; noRoomsHint: string;
  yourRoom: string; room: string; deck: string; join: string;
  cancelRoom: string; leaveRoom: string; waitingOpponent: string;
  opponentJoined: string; waitingHost: string; gameStarting: string;
  startingGame: string; yourDeck: string; opponent: string; host: string;
  shareRoomId: string; guestRoom: string; starting: string; startGame: string;
  cancel: string; opponentLeft: string; opponentLeftDesc: string;
  cancelConfirmTitle: string; cancelConfirmHostMsg: string;
  cancelConfirmGuestMsg: string; cancelConfirmLabelHost: string;
  cancelConfirmLabelGuest: string; stayInRoom: string;
  coinToss: string; coinCalling: string; heads: string; tails: string;
  coinResult: string; called: string; coin: string; choosesFirst: string;
  goFirst: string; goSecond: string; waitingCall: string; waitingChoose: string;
}

export interface AuthTranslations {
  login: string; register: string; createAccount: string;
  username: string; password: string; confirmPassword: string;
  usernamePlaceholder: string; passwordPlaceholder: string;
  confirmPasswordPlaceholder: string; loading: string;
  loginFailed: string; registerFailed: string;
}

export interface DeckTranslations {
  title: string; yourDecks: string; noDecks: string; selectDeck: string;
  yourDeck: string; opponentDeck: string; chooseYourDeck: string;
  chooseOpponentDeck: string; vsAgent: string; opponentWillChoose: string;
  startBattle: string; cancel: string; loading: string; createFirstDeck: string;
  decksAvailable: string; count: string;
  agentType: string; model: string; vs: string;
}

export interface LeaderboardTranslations {
  title: string; rank: string; player: string; rating: string;
  wins: string; losses: string; draws: string; total: string;
  winRate: string; noData: string; loading: string; matchHistory: string;
  date: string; result: string; deck: string; opponent: string;
  win: string; loss: string; draw: string; noMatches: string;
}
