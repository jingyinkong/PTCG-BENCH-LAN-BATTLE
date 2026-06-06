import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useGameStore } from '../stores/gameStore';
import ConfirmModal from './ConfirmModal';

export default function ActionPanel() {
  const { t } = useTranslation(['game', 'common', 'lobby']);
  const gt = (key: string) => t(key, { ns: 'game' });
  const { availableActions = [], executeAction, loading, isChoosingCard, isAgentThinking, vsAgent, turn, agentPlayer, isPvP, pvpPlayerId, leavePvPGame, opponentDisconnected, opponentLeft, reset } = useGameStore();
  const isMyTurn = isPvP ? turn === pvpPlayerId : vsAgent ? turn !== agentPlayer : true;
  const [showSurrenderConfirm, setShowSurrenderConfirm] = useState(false);

  const hasChooseCardActions = availableActions.some(a => a.actionType === 'ChooseCardAction');
  const displayActions = (isChoosingCard && hasChooseCardActions) || !isMyTurn
    ? []
    : availableActions.filter((a) => a.actionType !== 'ChooseCardAction');

  return (
    <div className="bg-slate-900 rounded-lg p-4 border border-slate-800">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">{t('game:gameInfo.actions')}</h3>
        <span className="text-[11px] font-mono text-slate-500">
          {isAgentThinking ? '…' : !isMyTurn ? t('common:status.waiting') : isChoosingCard ? t('common:status.choosing') : displayActions.length}
        </span>
      </div>

      <div className="space-y-1.5 max-h-60 overflow-y-auto">
        {isAgentThinking ? (
          <div className="flex flex-col items-center gap-2.5 py-6 text-center">
            <div className="relative w-10 h-10">
              <div className="absolute inset-0 rounded-full border border-sky-500/20 animate-ping" />
              <div className="absolute inset-1 rounded-full border border-sky-400/50 animate-spin" style={{ borderTopColor: 'transparent' }} />
              <svg className="absolute inset-0 m-auto w-4 h-4 text-sky-400" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 0 2h-1v1a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-1H2a1 1 0 0 1 0-2h1a7 7 0 0 1 7-7h1V5.73A2 2 0 0 1 10 4a2 2 0 0 1 2-2m0 7a5 5 0 0 0-5 5v2h10v-2a5 5 0 0 0-5-5M8.5 16a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3m7 0a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3z"/>
              </svg>
            </div>
            <p className="text-xs text-sky-400 font-medium">{t('game:gameInfo.agentThinking')}</p>
          </div>
        ) : !isMyTurn ? (
          <div className="flex flex-col items-center gap-2.5 py-6 text-center">
            <div className="w-10 h-10 rounded-full border border-amber-700/40 flex items-center justify-center">
              <svg className="w-4 h-4 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p className="text-xs text-amber-400/80">{t('game:gameInfo.opponentTurnWait')}</p>
          </div>
        ) : isChoosingCard ? (
          <div className="flex flex-col items-center gap-2.5 py-6 text-center">
            <div className="w-10 h-10 rounded-full border border-sky-700/40 flex items-center justify-center animate-pulse">
              <svg className="w-4 h-4 text-sky-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
            </div>
            <p className="text-xs text-sky-400">{t('game:gameInfo.choosingCard')}</p>
          </div>
        ) : displayActions.length === 0 ? (
          <div className="text-slate-600 text-xs text-center py-6">{t('common:status.noActions')}</div>
        ) : (
          displayActions.map((action, idx) => {
            const trueIdx = availableActions.indexOf(action);
            return (
              <button
                key={idx}
                onClick={() => executeAction(trueIdx)}
                disabled={loading || isAgentThinking || !isMyTurn}
                className="w-full text-left px-3 py-2.5 bg-slate-800 hover:bg-slate-700 border border-slate-700/60 hover:border-sky-500/40 disabled:opacity-40 disabled:cursor-not-allowed rounded-lg transition-all duration-150 group"
              >
                <div className="font-semibold text-xs text-slate-200 group-hover:text-sky-300 transition-colors">
                  {formatActionType(action.actionType, gt)}
                </div>
                <div className="text-[11px] text-slate-500 mt-0.5 leading-snug">
                  {formatActionDescription(action, gt)}
                </div>
              </button>
            );
          })
        )}
      </div>

      {/* PvP surrender / leave button */}
      {isPvP && (
        <div className="mt-3 pt-3 border-t border-slate-800">
          {opponentDisconnected ? (
            <div className="text-amber-400 text-xs text-center py-1">{t('lobby:opponentLeft')}</div>
          ) : (
            <button
              onClick={() => setShowSurrenderConfirm(true)}
              className="w-full px-3 py-2 bg-red-900/40 hover:bg-red-800/60 border border-red-800/40 hover:border-red-700/60 text-red-300 rounded-lg text-xs font-semibold transition-colors"
            >
              {t('game:gameInfo.surrender')}
            </button>
          )}
        </div>
      )}

      <ConfirmModal
        isOpen={showSurrenderConfirm}
        title={t('lobby:cancelConfirmTitle')}
        message={t('lobby:surrenderConfirmMsg')}
        confirmLabel={t('common:button.leaveGame')}
        cancelLabel={t('common:button.continueGame')}
        confirmVariant="danger"
        onConfirm={() => { setShowSurrenderConfirm(false); leavePvPGame(); }}
        onCancel={() => setShowSurrenderConfirm(false)}
      />

      {/* Opponent left modal — shown when the other player disconnects */}
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
            <p className="text-slate-400 text-sm mb-6">{t('lobby:opponentLeftGameDesc')}</p>
            <button
              onClick={() => { reset(); }}
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

const ACTION_TYPE_MAP: Record<string, string> = {
  AttackAction: 'attack', PlayPokemonAction: 'playPokemon',
  EvolvePokemonAction: 'evolve', AttachEnergyAction: 'attachEnergy',
  RetreatAction: 'retreat', UseAbilityAction: 'useAbility',
  UseItemAction: 'useItem', UseSupporterAction: 'useSupporter',
  UseToolAction: 'useTool', PutStadiumAction: 'putStadium',
  DiscardStadiumAction: 'discardStadium', UseStadiumAction: 'useStadium',
  PassTurn: 'pass', ChooseCardAction: 'chooseCard', EffectAction: 'effect',
};

function formatActionType(type: string, gt: (key: string) => string): string {
  const tKey = ACTION_TYPE_MAP[type];
  return tKey ? gt(`action.${tKey}`) : type;
}

function formatActionDescription(action: any, gt: (key: string) => string): string {
  const parts: string[] = [];
  if (action.source) parts.push(action.source);
  if (action.target) parts.push(`${gt('desc.arrow')} ${action.target}`);
  if (action.attack) parts.push(`${action.attack.name} · ${action.attack.damage} ${gt('desc.dmg')}`);
  if (action.ability) parts.push(`${gt('desc.ability')}: ${action.ability}`);
  if (action.position) parts.push(`${gt('desc.pos')} ${action.position}`);
  return parts.join(' · ') || '—';
}
