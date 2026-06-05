import { useState, useEffect } from 'react';
import { useGameStore } from './stores/gameStore';
import NavBar from './components/NavBar';
import GameBoard from './components/GameBoard';
import ActionPanel from './components/ActionPanel';
import GameLog from './components/GameLog';
import CardModal from './components/CardModal';
import CardSelectionOverlay from './components/CardSelectionOverlay';
import ReplayViewer from './components/ReplayViewer';
import DeckManager from './components/DeckManager';
import Leaderboard from './components/Leaderboard';
import DeckSelectModal from './components/DeckSelectModal';
import AuthPage from './components/AuthPage';
import LobbyPage from './components/LobbyPage';
import MatchHistory from './components/MatchHistory';
import { useAuthStore } from './stores/authStore';
import { Card } from './types/game';
import { useTranslation } from 'react-i18next';

type AppMode = 'home' | 'game' | 'replay' | 'decks' | 'leaderboard' | 'auth' | 'lobby' | 'history';

// Nav height offset — h-11 = 44px
const PAGE_WRAPPER = 'pt-11 min-h-screen bg-slate-950 text-slate-100';

function App() {
  const { t } = useTranslation(['common', 'game', 'lobby']);
  const { createGame, gameId, done, winner, loadCardImages, isPvP, opponentLeft, leavePvPGame } = useGameStore();
  const { isLoggedIn, fetchMe } = useAuthStore();
  const [selectedCard, setSelectedCard] = useState<{ card: Card; imageUrl?: string } | null>(null);
  const [mode, setMode] = useState<AppMode>('home');

  const [showDeckModal, setShowDeckModal] = useState(false);
  const [defaultDeck1, setDefaultDeck1] = useState<string | null>(null);
  const [defaultVsAgent, setDefaultVsAgent] = useState<boolean>(false);

  const handleOpenDeckModal = (preselectedDeck?: string, vsAgent?: boolean) => {
    setDefaultDeck1(preselectedDeck ?? null);
    setDefaultVsAgent(vsAgent ?? false);
    setShowDeckModal(true);
  };

  const handleStartBattle = (deck1?: string, deck2?: string, agent?: string, agentModel?: string) => {
    setShowDeckModal(false);
    createGame({ deck1, deck2, seed: Math.floor(Math.random() * 10000), agent, agentPlayer: 'player2', agentModel });
  };

  useEffect(() => { loadCardImages(); }, [loadCardImages]);
  useEffect(() => { if (gameId) setMode('game'); }, [gameId]);
  useEffect(() => { fetchMe(); }, [fetchMe]);

  const handleNavigate = (next: AppMode) => {
    if (next === 'game' && !gameId) return;
    setMode(next);
  };

  // ── Home ──────────────────────────────────────────────────────────────────
  const HomeScreen = (
    <div className="flex flex-col items-center justify-center" style={{ minHeight: 'calc(100vh - 44px)' }}>
      {/* Project identity */}
      <div className="mb-2 flex items-center gap-2">
        <span className="text-xs font-mono text-sky-500 uppercase tracking-widest px-2 py-0.5 rounded border border-sky-500/30 bg-sky-500/5">
          {t('common:nav.projectTag')}
        </span>
      </div>
      <h1 className="text-4xl font-bold text-slate-50 tracking-tight mb-2">
        Open-PTCG
      </h1>
      <p className="text-slate-400 mb-8 text-sm max-w-sm text-center leading-relaxed">
        {t('common:home.description')}
      </p>

      {/* Action buttons */}
      <div className="flex flex-col sm:flex-row items-center gap-3">
        <button
          onClick={() => handleOpenDeckModal()}
          className="px-6 py-2.5 bg-sky-600 hover:bg-sky-500 text-white rounded-lg font-semibold text-sm transition-colors shadow-md"
        >
          {t('common:button.newGame')}
        </button>
        <button
          onClick={() => handleOpenDeckModal(undefined, true)}
          className="px-6 py-2.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 hover:border-sky-500/50 text-slate-200 rounded-lg font-semibold text-sm transition-colors flex items-center gap-2"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="currentColor" className="text-sky-400">
            <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 0 2h-1v1a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-1H2a1 1 0 0 1 0-2h1a7 7 0 0 1 7-7h1V5.73A2 2 0 0 1 10 4a2 2 0 0 1 2-2m0 7a5 5 0 0 0-5 5v2h10v-2a5 5 0 0 0-5-5M8.5 16a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3m7 0a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3z"/>
          </svg>
          {t('common:nav.vsAI')}
        </button>
        <button
          onClick={() => setMode('replay')}
          className="px-6 py-2.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 hover:border-sky-500/50 text-slate-200 rounded-lg font-semibold text-sm transition-colors flex items-center gap-2"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-sky-400">
            <polygon points="5 3 19 12 5 21 5 3" />
          </svg>
          {t('common:nav.replay')}
        </button>
        {isLoggedIn && (
          <button
            onClick={() => setMode('lobby')}
            className="px-6 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-semibold text-sm transition-colors shadow-md flex items-center gap-2"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-emerald-200">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" />
            </svg>
            {t('common:nav.lanBattle')}
          </button>
        )}
        <button
          onClick={() => setMode('leaderboard')}
          className="px-6 py-2.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 hover:border-sky-500/50 text-slate-200 rounded-lg font-semibold text-sm transition-colors flex items-center gap-2"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-sky-400">
            <line x1="18" y1="20" x2="18" y2="10" /><line x1="12" y1="20" x2="12" y2="4" /><line x1="6" y1="20" x2="6" y2="14" />
          </svg>
          {t('common:nav.leaderboard')}
        </button>
      </div>

      {/* Quick links */}
      <div className="mt-10 flex items-center gap-6 text-xs text-slate-600">
        <button onClick={() => setMode('decks')} className="hover:text-slate-400 transition-colors">
          {t('common:button.browseDecks')}
        </button>
        <span className="text-slate-800">·</span>
        <a href="https://github.com" target="_blank" rel="noreferrer" className="hover:text-slate-400 transition-colors">
          {t('common:button.documentation')}
        </a>
      </div>
    </div>
  );

  // ── Game over ─────────────────────────────────────────────────────────────
  const GameOverScreen = (
    <div className="flex flex-col items-center justify-center" style={{ minHeight: 'calc(100vh - 44px)' }}>
      <div className="bg-slate-900 border border-slate-700 rounded-xl p-10 text-center max-w-sm w-full shadow-xl">
        <div className="text-xs font-mono text-slate-500 uppercase tracking-widest mb-3">{t('game:result.gameResult')}</div>
        <h2 className="text-2xl font-bold text-slate-50 mb-1">
          {winner ? `${winner === 'player1' ? t('game:player.p1') : t('game:player.p2')} ${t('game:result.wins')}` : t('game:result.gameOver')}
        </h2>
        {winner && (
          <p className="text-sm text-slate-400 mb-6">
            {winner === 'player1' ? t('game:player.youP1') : t('game:player.p2')} {t('game:result.tookAllPrizes')}
          </p>
        )}
        <div className="flex flex-col gap-2 mt-6">
          <button
            onClick={() => { useGameStore.getState().reset(); handleOpenDeckModal(); }}
            className="w-full px-6 py-2.5 bg-sky-600 hover:bg-sky-500 text-white rounded-lg font-semibold text-sm transition-colors"
          >
            {t('common:button.playAgain')}
          </button>
          <button
            onClick={() => { useGameStore.getState().reset(); setMode('home'); }}
            className="w-full px-6 py-2.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 rounded-lg font-semibold text-sm transition-colors"
          >
            {t('common:button.backToHome')}
          </button>
        </div>
      </div>
    </div>
  );

  // ── Active game board ─────────────────────────────────────────────────────
  const GameScreen = (
    <div className="p-2 flex flex-col overflow-hidden" style={{ height: 'calc(100vh - 44px)' }}>
      <div className="grid grid-cols-12 gap-3 flex-1 min-h-0">
        <div className="col-span-9 min-h-0 overflow-hidden">
          <GameBoard onCardClick={(card, imageUrl) => setSelectedCard({ card, imageUrl })} />
        </div>
        <div className="col-span-3 flex flex-col gap-3 min-h-0">
          <div className="flex-shrink-0"><ActionPanel /></div>
          <div className="flex-1 min-h-0"><GameLog /></div>
        </div>
      </div>
    </div>
  );

  // ── Route ─────────────────────────────────────────────────────────────────
  let body: React.ReactNode;
  if (mode === 'leaderboard') {
    body = <Leaderboard />;
  } else if (mode === 'replay') {
    body = <ReplayViewer onBack={() => setMode('home')} />;
  } else if (mode === 'decks') {
    body = <DeckManager onPlayWithDeck={(deckId) => handleOpenDeckModal(deckId)} />;
  } else if (mode === 'auth') {
    body = <AuthPage onBack={() => setMode('home')} />;
  } else if (mode === 'lobby') {
    body = isLoggedIn ? <LobbyPage /> : <AuthPage onBack={() => setMode('home')} />;
  } else if (mode === 'history') {
    body = isLoggedIn ? <MatchHistory /> : <AuthPage onBack={() => setMode('home')} />;
  } else if (mode === 'game' && gameId) {
    body = done ? GameOverScreen : GameScreen;
  } else {
    body = HomeScreen;
  }

  return (
    <div className={PAGE_WRAPPER}>
      <NavBar
        mode={mode}
        onNavigate={handleNavigate}
        onBattleHuman={() => handleOpenDeckModal(undefined, false)}
        onBattleAI={() => handleOpenDeckModal(undefined, true)}
      />
      {body}
      <DeckSelectModal
        isOpen={showDeckModal}
        onClose={() => setShowDeckModal(false)}
        onConfirm={handleStartBattle}
        defaultDeck1={defaultDeck1}
        defaultVsAgent={defaultVsAgent}
      />
      <CardSelectionOverlay />
      {selectedCard && (
        <CardModal
          card={selectedCard.card}
          imageUrl={selectedCard.imageUrl}
          isOpen={true}
          onClose={() => setSelectedCard(null)}
        />
      )}

      {/* Opponent left popup — PvP mode */}
      {isPvP && opponentLeft && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-600 rounded-xl p-8 max-w-sm w-full mx-4 text-center shadow-2xl">
            <div className="w-14 h-14 mx-auto mb-4 rounded-full bg-amber-500/20 flex items-center justify-center">
              <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none"
                stroke="#f59e0b" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
            </div>
            <h3 className="text-xl font-bold text-slate-50 mb-2">{t('lobby:opponentLeft')}</h3>
            <p className="text-slate-400 text-sm mb-6">
              {t('lobby:opponentLeftGameDesc')}
            </p>
            <button
              onClick={() => {
                leavePvPGame();
                setMode('home');
              }}
              className="w-full px-6 py-2.5 bg-sky-600 hover:bg-sky-500 text-white rounded-lg font-semibold text-sm transition-colors"
            >
              {t('common:button.backToHome')}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
