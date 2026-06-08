import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useGameStore } from '../stores/gameStore';
import { api } from '../services/api';
import EnergyIcon from './EnergyIcon';
import { ENERGY_CODE_TO_TYPE } from './DeckCard';

interface DeckDetail {
  id: string;
  displayName: string;
  pokemon: { count: number; name: string; set: string; number: string }[];
  pokemonCount: number;
  trainer: { count: number; name: string; set: string; number: string }[];
  trainerCount: number;
  energy: { count: number; name: string; set: string; number: string }[];
  energyCount: number;
  energyTypes: string[];
}

interface Props {
  deckId: string;
  isOpen: boolean;
  onClose: () => void;
}

export default function DeckDetailModal({ deckId, isOpen, onClose }: Props) {
  const { t } = useTranslation(['deck', 'common']);
  const { cardImages } = useGameStore();
  const [deck, setDeck] = useState<DeckDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!isOpen || !deckId) return;
    setLoading(true);
    setError('');
    api.getDeckDetail(deckId)
      .then(data => { setDeck(data); setError(''); })
      .catch((e: any) => { setDeck(null); setError(e?.response?.data?.detail || e?.message || String(e)); })
      .finally(() => setLoading(false));
  }, [isOpen, deckId]);

  if (!isOpen) return null;

  const energyTypeNames = (deck?.energyTypes ?? []).map(c => ENERGY_CODE_TO_TYPE[c] ?? 'colorless');

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="absolute inset-0 bg-black/80 backdrop-blur-sm" />
      <div
        className="relative bg-slate-900 border border-slate-700 rounded-xl w-full max-w-lg flex flex-col shadow-2xl"
        style={{ maxHeight: 'calc(100vh - 80px)' }}
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 flex-shrink-0">
          <div>
            <h2 className="text-base font-semibold text-slate-100">{deck?.displayName ?? deckId}</h2>
            <div className="flex gap-2 mt-1">
              {deck && (
                <span className="text-[11px] text-slate-500 font-mono">
                  {deck.pokemonCount}P · {deck.trainerCount}T · {deck.energyCount}E
                </span>
              )}
            </div>
          </div>
          <button onClick={onClose} className="text-slate-600 hover:text-slate-300 transition-colors p-1 rounded">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {loading ? (
            <div className="text-center text-slate-500 py-8 text-sm">{t('common:status.loading')}</div>
          ) : !deck ? (
            <div className="text-center py-8"><p className="text-sm text-red-400">{t('deck:loadFailed')}</p>{error && <p className="text-xs text-slate-600 mt-2 font-mono">{error}</p>}</div>
          ) : (
            <>
              {/* Pokémon section */}
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <h3 className="text-xs font-semibold text-sky-400 uppercase tracking-wider">{t('deck:pokemonSection')}</h3>
                  <span className="text-[10px] text-slate-600 font-mono">({deck.pokemonCount})</span>
                </div>
                <div className="space-y-1">
                  {deck.pokemon.map((p, i) => (
                    <div key={i} className="flex items-center gap-3 bg-slate-800/60 rounded-lg px-3 py-2">
                      {cardImages[p.name] && (
                        <img src={cardImages[p.name]} alt={p.name} className="w-10 h-14 rounded object-cover flex-shrink-0" />
                      )}
                      <div className="flex-1 min-w-0">
                        <p className="text-xs text-slate-200 font-medium truncate">{p.name}</p>
                        <p className="text-[10px] text-slate-600 font-mono">{p.set} {p.number}</p>
                      </div>
                      <span className="text-xs text-slate-400 font-mono font-bold flex-shrink-0">{p.count}×</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Trainer section */}
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <h3 className="text-xs font-semibold text-pink-400 uppercase tracking-wider">{t('deck:trainerSection')}</h3>
                  <span className="text-[10px] text-slate-600 font-mono">({deck.trainerCount})</span>
                </div>
                <div className="space-y-1">
                  {deck.trainer.map((tCard, i) => (
                    <div key={i} className="flex items-center justify-between bg-slate-800/60 rounded-lg px-3 py-2">
                      <div className="flex items-center gap-3">
                        {cardImages[tCard.name] && (
                          <img src={cardImages[tCard.name]} alt={tCard.name} className="w-10 h-14 rounded object-cover flex-shrink-0" />
                        )}
                        <div>
                          <p className="text-xs text-slate-300 font-medium">{tCard.name}</p>
                          <p className="text-[10px] text-slate-600 font-mono">{tCard.set} {tCard.number}</p>
                        </div>
                      </div>
                      <span className="text-xs text-slate-400 font-mono font-bold">{tCard.count}×</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Energy section */}
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <h3 className="text-xs font-semibold text-amber-400 uppercase tracking-wider">{t('deck:energySection')}</h3>
                  <span className="text-[10px] text-slate-600 font-mono">({deck.energyCount})</span>
                </div>
                <div className="flex items-center gap-3 bg-slate-800/60 rounded-lg px-3 py-3">
                  <div className="flex gap-1.5">
                    {energyTypeNames.map((type, i) => (
                      <EnergyIcon key={i} type={type} size={22} />
                    ))}
                  </div>
                  <span className="text-xs text-slate-400 font-mono">{deck.energyCount} {t('deck:energyCards')}</span>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-slate-800 flex-shrink-0 flex justify-end">
          <button onClick={onClose}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm font-medium transition-colors">
            {t('common:button.close')}
          </button>
        </div>
      </div>
    </div>
  );
}
