import { useState } from 'react';
import { Card, TrainerCard } from '../types/game';
import { useGameStore } from '../stores/gameStore';
import { useDragStore, MatchedAction } from '../stores/dragStore';
import PlayerArea from './PlayerArea';

interface Props {
  onCardClick?: (card: Card, imageUrl?: string) => void;
}

const PLAY_ZONE_TYPES = ['UseItemAction', 'UseSupporterAction', 'PutStadiumAction'];

function getPlayZoneAction(matched: MatchedAction[]): MatchedAction | undefined {
  return matched.find(({ action }) => PLAY_ZONE_TYPES.includes(action.actionType));
}

function getPlayZoneLabel(matched: MatchedAction[]): string {
  const types = matched.map((a) => a.action.actionType);
  if (types.includes('UseSupporterAction')) return 'Play Supporter';
  if (types.includes('UseItemAction')) return 'Play Item';
  if (types.includes('PutStadiumAction')) return 'Play Stadium';
  return 'Play Card';
}

export default function GameBoard({ onCardClick }: Props) {
  const { state, turn, cardImages, executeAction, vsAgent, agentPlayer, agentType, isPvP, pvpPlayerId } = useGameStore();
  const { isDragging, matchedActions } = useDragStore();
  const [isOver, setIsOver] = useState(false);

  if (!state) return null;

  // In PvP mode, swap perspective so each player sees themselves at the bottom
  const selfPlayer = isPvP && pvpPlayerId === 'player2' ? state.player2 : state.player1;
  const oppPlayer = isPvP && pvpPlayerId === 'player2' ? state.player1 : state.player2;
  const selfName = isPvP ? (pvpPlayerId === 'player1' ? 'You (P1)' : 'You (P2)') : 'Player 1';
  const oppName = isPvP ? (pvpPlayerId === 'player1' ? 'Opponent (P2)' : 'Opponent (P1)') : 'Player 2';

  // Display turn info with PvP-aware labels
  const displayTurn = isPvP
    ? (turn === pvpPlayerId ? `Your Turn` : `Opponent's Turn`)
    : (turn ?? '—');

  const stadiumCard = state.stadium && state.stadium.length > 0 ? state.stadium[0] : null;

  const handleStadiumClick = () => {
    if (!stadiumCard || !onCardClick) return;
    const asTrainerCard: TrainerCard = { name: stadiumCard.name, trainerType: 'STADIUM' };
    onCardClick(asTrainerCard, cardImages[stadiumCard.name]);
  };

  const isPlayZone = isDragging && !!getPlayZoneAction(matchedActions);

  return (
    <div
      className={[
        'relative grid h-full min-h-0 grid-rows-[34px_minmax(0,1fr)_24px_minmax(0,1fr)] gap-2 rounded-xl transition-all duration-150 overflow-hidden',
        isPlayZone ? 'ring-1 ring-emerald-500/40' : '',
        isOver && isPlayZone ? 'ring-emerald-400/60 shadow-lg shadow-emerald-500/10' : '',
      ].join(' ')}
      onDragOver={(e) => { if (isPlayZone) e.preventDefault(); }}
      onDragEnter={(e) => { if (isPlayZone) { e.preventDefault(); setIsOver(true); } }}
      onDragLeave={(e) => {
        if (!e.relatedTarget || !e.currentTarget.contains(e.relatedTarget as Node)) setIsOver(false);
      }}
      onDrop={(e) => {
        if (!isPlayZone) return;
        e.preventDefault();
        setIsOver(false);
        const action = getPlayZoneAction(matchedActions);
        if (action) executeAction(action.actionIndex);
      }}
    >
      {/* Drop overlay */}
      {isPlayZone && isOver && (
        <div className="absolute inset-0 bg-emerald-500/5 rounded-xl pointer-events-none flex items-end justify-center pb-36 z-20">
          <span className="bg-slate-950/95 text-emerald-400 text-xs font-semibold uppercase tracking-widest px-4 py-1.5 rounded-lg border border-emerald-500/40">
            {getPlayZoneLabel(matchedActions)}
          </span>
        </div>
      )}

      {/* Game info bar */}
      <div className="bg-slate-900 rounded-lg px-4 py-1.5 flex items-center justify-between text-sm border border-slate-800 min-h-0">
        <div className="text-slate-400 text-xs">
          Turn: <span className={`font-mono font-medium uppercase ml-1 ${displayTurn === 'Your Turn' ? 'text-emerald-400' : 'text-sky-400'}`}>{displayTurn}</span>
        </div>
        <div className="text-slate-500 text-xs">
          Step: <span className="text-slate-300 font-mono font-medium ml-1">{state.timestep ?? '—'}</span>
        </div>
      </div>

      {/* Opponent (top) */}
      <PlayerArea
        player={oppPlayer}
        isOpponent
        playerName={oppName}
        cardImages={cardImages}
        onCardClick={onCardClick}
        isAgent={vsAgent && agentPlayer === 'player2'}
        agentType={vsAgent && agentPlayer === 'player2' ? agentType : null}
      />

      {/* Stadium divider */}
      <div className="flex items-center gap-3 px-2 min-h-0">
        <div className="h-px flex-1 bg-slate-800" />
        <div
          className={[
            'flex items-center gap-2 px-3 py-1 rounded-full border transition-all duration-150',
            stadiumCard
              ? 'border-sky-500/50 bg-sky-950/20 cursor-pointer hover:border-sky-400 hover:bg-sky-950/40'
              : 'border-slate-800 bg-slate-950/40',
          ].join(' ')}
          onClick={stadiumCard ? handleStadiumClick : undefined}
          title={stadiumCard ? `Click to view ${stadiumCard.name}` : undefined}
        >
          <span className="text-[10px] uppercase tracking-widest text-slate-600 font-semibold">
            Stadium
          </span>
          {stadiumCard && (
            <span className="text-xs text-sky-400 font-medium">— {stadiumCard.name}</span>
          )}
        </div>
        <div className="h-px flex-1 bg-slate-800" />
      </div>

      {/* Self (bottom) */}
      <PlayerArea
        player={selfPlayer}
        isOpponent={false}
        playerName={selfName}
        cardImages={cardImages}
        onCardClick={onCardClick}
      />
    </div>
  );
}
