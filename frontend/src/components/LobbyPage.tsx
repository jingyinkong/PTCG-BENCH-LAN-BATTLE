import { useState, useEffect, useCallback, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { api, RoomInfo } from '../services/api';
import { useAuthStore } from '../stores/authStore';
import { useGameStore } from '../stores/gameStore';
import DeckSelectModal from './DeckSelectModal';
import ConfirmModal from './ConfirmModal';

export default function LobbyPage() {
  const { t } = useTranslation(['lobby', 'common']);
  const [rooms, setRooms] = useState<RoomInfo[]>([]);
  const [myRoom, setMyRoom] = useState<RoomInfo | null>(null);
  const [showDeckModal, setShowDeckModal] = useState(false);
  const [deckAction, setDeckAction] = useState<'create' | 'join' | null>(null);
  const [targetRoomId, setTargetRoomId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [starting, setStarting] = useState(false);
  const [opponentLeft, setOpponentLeft] = useState(false);
  const [showCancelConfirm, setShowCancelConfirm] = useState(false);
  const { user } = useAuthStore();
  const { startPvPGame, reset, coinTossResult, sendCoinTossCall, sendCoinTossChoose } = useGameStore();
  const pollFailCount = useRef(0);
  const hadGuest = useRef(false);

  const fetchRooms = useCallback(async () => {
    try {
      const data = await api.listRooms();
      setRooms(data.rooms);
    } catch {}
  }, []);

  // Recover myRoom from server list after page refresh / navigation
  useEffect(() => {
    if (!myRoom && rooms.length > 0) {
      const ownRoom = rooms.find(r => r.is_own);
      if (ownRoom) setMyRoom(ownRoom);
    }
  }, [rooms, myRoom]);

  // Poll for room list (guest view)
  useEffect(() => {
    fetchRooms();
    const interval = setInterval(fetchRooms, 3000);
    return () => clearInterval(interval);
  }, [fetchRooms]);

  // Poll my own room for status changes (host or guest)
  useEffect(() => {
    if (!myRoom) return;
    const roomId = myRoom.id;
    const myUserId = user?.id;
    const isHost = myRoom.host_user_id === myUserId;
    // Track whether guest has ever been present using ref
    if (myRoom.guest_user_id != null) {
      hadGuest.current = true;
    }

    const check = setInterval(async () => {
      try {
        const data = await api.getRoom(roomId);
        const room = data.room;
        pollFailCount.current = 0; // reset on success
        setMyRoom(room as RoomInfo);

        // Host: detect when guest leaves (guest_user_id becomes null)
        if (isHost && hadGuest.current && !room.guest_user_id && room.status === 'waiting') {
          clearInterval(check);
          setOpponentLeft(true);
          return;
        }

        // Guest: detect when host starts the game
        if (room.status === 'playing' && myUserId && room.guest_user_id === myUserId) {
          clearInterval(check);
          startPvPGame(roomId, 'player2');
        }
      } catch {
        pollFailCount.current += 1;
        // Room deleted (host cancelled) → opponent left
        if (pollFailCount.current >= 3) {
          clearInterval(check);
          setOpponentLeft(true);
        }
      }
    }, 2000);
    return () => clearInterval(check);
  }, [myRoom?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleCreateRoom = () => {
    reset();
    setDeckAction('create');
    setTargetRoomId(null);
    setShowDeckModal(true);
  };

  const handleJoinRoom = (roomId: string) => {
    reset();
    setDeckAction('join');
    setTargetRoomId(roomId);
    setShowDeckModal(true);
  };

  const handleDeckConfirm = async (deck1?: string) => {
    setShowDeckModal(false);
    if (!deck1) return;
    setLoading(true);
    try {
      if (deckAction === 'create') {
        const data = await api.createRoom(deck1);
        setMyRoom(data.room);
      } else if (deckAction === 'join' && targetRoomId) {
        const data = await api.joinRoom(targetRoomId, deck1);
        setMyRoom(data.room);
      }
    } catch (e: any) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleStartGame = async () => {
    if (!myRoom) return;
    setStarting(true);
    try {
      await api.startRoom(myRoom.id);
      startPvPGame(myRoom.id, 'player1');
    } catch (e: any) {
      console.error(e);
    } finally {
      setStarting(false);
    }
  };

  const handleCancelRoom = async () => {
    if (myRoom) {
      try { await api.leaveRoom(myRoom.id); } catch {}
      setMyRoom(null);
    }
  };

  const isHost = myRoom && user && myRoom.host_user_id === user.id;
  const isGuest = myRoom && user && myRoom.guest_user_id === user.id;
  const guestJoined = myRoom?.guest_user_id != null;

  // Show waiting screen (host or guest waiting)
  if (myRoom) {
    const statusText = myRoom.status === 'playing'
      ? t('lobby:gameStarting')
      : isHost
        ? guestJoined
          ? t('lobby:opponentJoined')
          : t('lobby:waitingOpponent')
        : t('lobby:waitingHost');

    return (
      <div className="flex items-center justify-center" style={{ minHeight: 'calc(100vh - 44px)' }}>
        <div className="bg-slate-900 border border-slate-700 rounded-xl p-8 w-full max-w-md text-center shadow-xl">
          {myRoom.status !== 'playing' && (
            <div className="w-12 h-12 mx-auto mb-4 rounded-full border-4 border-sky-500 border-t-transparent animate-spin" />
          )}
          {myRoom.status === 'playing' && (
            <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-emerald-500/20 flex items-center justify-center">
              <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none"
                stroke="#34d399" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12" />
              </svg>
            </div>
          )}
          <h2 className="text-xl font-bold text-slate-50 mb-2">
            {myRoom.status === 'playing' ? t('lobby:startingGame') : isHost ? t('lobby:yourRoom') : t('lobby:guestRoom')}
          </h2>
          <p className="text-slate-400 text-sm mb-1">{statusText}</p>
          <p className="text-slate-500 text-xs mb-1">
            {t('lobby:room')} <span className="font-mono text-sky-400">#{myRoom.id}</span>
          </p>
          <p className="text-slate-500 text-xs mb-1">
            {t('lobby:yourDeck')}: {isHost ? myRoom.host_deck : myRoom.guest_deck}
          </p>
          {isHost && guestJoined && (
            <p className="text-slate-500 text-xs mb-6">
              {t('lobby:opponent')}: <span className="text-amber-400">{myRoom.guest_username}</span> &middot; {t('lobby:deck')}: {myRoom.guest_deck}
            </p>
          )}
          {isHost && !guestJoined && (
            <p className="text-slate-600 text-xs mb-6">{t('lobby:shareRoomId')}</p>
          )}
          {isGuest && (
            <p className="text-slate-500 text-xs mb-6">
              {t('lobby:host')}: <span className="text-sky-400">{myRoom.host_username}</span>
            </p>
          )}

          {/* ── Coin Toss Interactive UI ── */}
          {coinTossResult && coinTossResult.phase === 'call' && (
            <div className="mb-6 p-4 bg-amber-950/30 border border-amber-700/50 rounded-lg">
              <p className="text-amber-300 text-sm font-semibold mb-1">{t('lobby:coinToss')}</p>
              <p className="text-slate-400 text-xs mb-3">
                {coinTossResult.caller_name} {t('lobby:coinCalling')}
              </p>
              {coinTossResult.caller === (isHost ? 'player1' : 'player2') ? (
                <div className="flex gap-3 justify-center">
                  <button onClick={() => sendCoinTossCall('heads')}
                    className="px-6 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-lg font-semibold text-sm transition-colors">
                    {t('lobby:heads')}
                  </button>
                  <button onClick={() => sendCoinTossCall('tails')}
                    className="px-6 py-2 bg-slate-600 hover:bg-slate-500 text-white rounded-lg font-semibold text-sm transition-colors">
                    {t('lobby:tails')}
                  </button>
                </div>
              ) : (
                <p className="text-slate-500 text-xs">{t('lobby:waitingCall', { name: coinTossResult.caller_name })}</p>
              )}
            </div>
          )}

          {coinTossResult && coinTossResult.phase === 'result' && (
            <div className="mb-6 p-4 bg-amber-950/30 border border-amber-700/50 rounded-lg">
              <p className="text-amber-300 text-sm font-semibold mb-1">{t('lobby:coinResult')}</p>
              <p className="text-slate-300 text-xs mb-1">
                {coinTossResult.caller_name} {t('lobby:called')} <span className="font-bold text-white">{coinTossResult.caller_choice}</span>
                {' → '} {t('lobby:coin')}: <span className="font-bold text-amber-400">{coinTossResult.coin}</span>
              </p>
              <p className="text-slate-400 text-xs mb-3">
                {coinTossResult.chooser_name} {t('lobby:choosesFirst')}
              </p>
              {coinTossResult.chooser === (isHost ? 'player1' : 'player2') ? (
                <div className="flex gap-3 justify-center">
                  <button onClick={() => sendCoinTossChoose('first')}
                    className="px-6 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-semibold text-sm transition-colors">
                    {t('lobby:goFirst')}
                  </button>
                  <button onClick={() => sendCoinTossChoose('second')}
                    className="px-6 py-2 bg-slate-600 hover:bg-slate-500 text-white rounded-lg font-semibold text-sm transition-colors">
                    {t('lobby:goSecond')}
                  </button>
                </div>
              ) : (
                <p className="text-slate-500 text-xs">{t('lobby:waitingChoose', { name: coinTossResult.chooser_name })}</p>
              )}
            </div>
          )}

          <div className="flex gap-3 justify-center">
            {/* Host: Start Game button (only when guest has joined and room is waiting) */}
            {isHost && guestJoined && myRoom.status === 'waiting' && (
              <button onClick={handleStartGame} disabled={starting}
                className="px-6 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-700 text-white rounded-lg font-semibold text-sm transition-colors">
                {starting ? t('lobby:starting') : t('lobby:startGame')}
              </button>
            )}
            <button onClick={() => setShowCancelConfirm(true)}
              className="px-6 py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg font-semibold text-sm transition-colors">
              {t('lobby:cancel')}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-2xl mx-auto" style={{ minHeight: 'calc(100vh - 44px)' }}>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-slate-50">{t('lobby:title')}</h2>
        <button onClick={handleCreateRoom} disabled={loading}
          className="px-4 py-2 bg-sky-600 hover:bg-sky-500 disabled:bg-slate-700 text-white rounded-lg font-semibold text-sm transition-colors">
          {t('lobby:createRoom')}
        </button>
      </div>

      {rooms.length === 0 ? (
        <div className="text-center text-slate-500 py-16">
          <p className="text-lg">{t('lobby:noRooms')}</p>
          <p className="text-sm mt-2">{t('lobby:noRoomsHint')}</p>
        </div>
      ) : (
        <div className="space-y-3">
          {rooms.filter(r => r.is_own).map((room) => (
            <div key={room.id}
              className="bg-sky-950 border border-sky-700 rounded-lg p-4 flex items-center justify-between">
              <div>
                <div className="text-sky-200 font-semibold text-sm">{t('lobby:yourRoom')} #{room.id}</div>
                <div className="text-sky-400 text-xs mt-1">
                  {t('lobby:deck')}: {room.host_deck || '—'} &middot; {room.guest_user_id ? `${t('lobby:opponent')}: ${room.guest_username}` : t('lobby:waitingOpponent')}
                </div>
              </div>
              <button onClick={() => setShowCancelConfirm(true)}
                className="px-4 py-1.5 bg-red-700 hover:bg-red-600 text-white rounded-lg text-sm font-medium transition-colors">
                {t('lobby:cancelRoom')}
              </button>
            </div>
          ))}
          {rooms.filter(r => !r.is_own).map((room) => (
            <div key={room.id}
              className="bg-slate-900 border border-slate-700 rounded-lg p-4 flex items-center justify-between">
              <div>
                <div className="text-slate-200 font-semibold text-sm">{t('lobby:roomOf', { name: room.host_username })}</div>
                <div className="text-slate-500 text-xs mt-1">
                  {t('lobby:deck')}: {room.host_deck || '—'} &middot; {t('lobby:room')} #{room.id}
                </div>
              </div>
              <button onClick={() => handleJoinRoom(room.id)} disabled={loading}
                className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-700 text-white rounded-lg text-sm font-medium transition-colors">
                {t('lobby:join')}
              </button>
            </div>
          ))}
        </div>
      )}

      <DeckSelectModal isOpen={showDeckModal} onClose={() => setShowDeckModal(false)}
        onConfirm={handleDeckConfirm} defaultVsAgent={false} pvpMode={true} />

      {/* Opponent left popup — waiting phase */}
      {opponentLeft && (
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
              {t('lobby:opponentLeftDesc')}
            </p>
            <button
              onClick={() => {
                setOpponentLeft(false);
                setMyRoom(null);
                reset();
              }}
              className="w-full px-6 py-2.5 bg-sky-600 hover:bg-sky-500 text-white rounded-lg font-semibold text-sm transition-colors"
            >
              {t('common:button.backToLobby')}
            </button>
          </div>
        </div>
      )}

      {/* Cancel room confirmation */}
      <ConfirmModal
        isOpen={showCancelConfirm}
        title={t('lobby:cancelConfirmTitle')}
        message={isHost ? t('lobby:cancelConfirmHostMsg') : t('lobby:cancelConfirmGuestMsg')}
        confirmLabel={isHost ? t('lobby:cancelConfirmLabelHost') : t('lobby:cancelConfirmLabelGuest')}
        cancelLabel={t('lobby:stayInRoom')}
        confirmVariant="danger"
        onConfirm={() => { setShowCancelConfirm(false); handleCancelRoom(); }}
        onCancel={() => setShowCancelConfirm(false)}
      />
    </div>
  );
}
