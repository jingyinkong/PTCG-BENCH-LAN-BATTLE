import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useDeckStore } from '../stores/deckStore';
import { useGameStore } from '../stores/gameStore';
import DeckCard from './DeckCard';
import { api } from '../services/api';
import DeckDetailModal from './DeckDetailModal';

interface DeckManagerProps {
  onPlayWithDeck: (deckId: string) => void;
}

export default function DeckManager({ onPlayWithDeck }: DeckManagerProps) {
  const { t } = useTranslation(['deck', 'common']);
  const { decks, loading, loadDecks } = useDeckStore();
  const { cardImages, loadCardImages } = useGameStore();
  const [detailDeckId, setDetailDeckId] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [refreshMsg, setRefreshMsg] = useState('');
  const [progress, setProgress] = useState(0);
  const [deckRefreshing, setDeckRefreshing] = useState(false);
  const [deckRefreshMsg, setDeckRefreshMsg] = useState('');
  const [deckProgress, setDeckProgress] = useState(0);

  useEffect(() => { loadDecks(); }, [loadDecks]);

  return (
    <div className="p-6 pb-10 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6 flex items-end justify-between">
        <div>
          <div className="text-[11px] font-mono text-sky-500 uppercase tracking-widest mb-1">{t('common:nav.decks')}</div>
          <h2 className="text-xl font-bold text-slate-50">{t('deck:yourDecks')}</h2>
          <p className="text-xs text-slate-500 mt-1">
            {decks.length > 0
              ? t('deck:decksAvailable', { count: decks.length })
              : t('deck:noDecks')}
          </p>
        </div>
        <div className="flex items-center gap-4">
          {decks.length > 0 && (
            <span className="px-3 py-1 rounded-md bg-slate-800 border border-slate-700 text-slate-500 text-xs font-mono flex-shrink-0">
              {t('deck:count', { count: decks.length })}
            </span>
          )}
        </div>
      </div>


      {/* Action buttons */}
      <div className="mb-6 flex items-center gap-3">
        <button onClick={async () => {
          setDeckRefreshing(true); setDeckRefreshMsg(''); setDeckProgress(0);
          try {
            const r = await api.refreshDecks();
            if (!r?.success) { setDeckRefreshMsg(r?.error || t('deck:refreshFailed')); setDeckRefreshing(false); return; }
            const poll = setInterval(async () => {
              try {
                const s = await api.getDeckRefreshStatus();
                setDeckProgress(s?.total > 0 ? Math.round((s.progress / s.total) * 100) : 0);
                setDeckRefreshMsg(s?.message || '');
                if (s?.done) { clearInterval(poll); setDeckRefreshing(false);
                  if (s?.error) setDeckRefreshMsg(t('deck:refreshFailed'));
                  else { setDeckRefreshMsg(t('deck:deckRefreshDone')); loadDecks(); }
                }
              } catch { clearInterval(poll); setDeckRefreshing(false); }
            }, 1500);
          } catch { setDeckRefreshMsg(t('deck:refreshFailed')); setDeckRefreshing(false); }
        }}
          disabled={deckRefreshing || refreshing}
          className="px-3 py-1.5 rounded-md bg-slate-800 border border-slate-700 text-slate-400 hover:text-emerald-400 hover:border-emerald-700/50 text-xs font-medium transition-colors disabled:opacity-50"
        >{deckRefreshing ? t('deck:deckRefreshing') : t('deck:refreshDecks')}</button>
        {deckRefreshing && <div className="flex items-center gap-1.5"><div className="w-16 h-1 bg-slate-700 rounded-full overflow-hidden"><div className="h-full bg-emerald-500 transition-all duration-500" style={{width:`${deckProgress}%`}}/></div><span className="text-[10px] text-slate-500 font-mono">{deckProgress}%</span></div>}
        {!deckRefreshing && deckRefreshMsg && <span className="text-[11px] text-slate-500">{deckRefreshMsg}</span>}

        <button onClick={async () => {
          setRefreshing(true); setRefreshMsg(''); setProgress(0);
          try {
            const r = await api.refreshCardImages();
            if (!r?.success) { setRefreshMsg(r?.error || t('deck:refreshFailed')); setRefreshing(false); return; }
            const poll = setInterval(async () => {
              try {
                const s = await api.getDownloadStatus();
                setProgress(s?.total > 0 ? Math.round((s.progress / s.total) * 100) : 0);
                setRefreshMsg(s?.message || '');
                if (s?.done) { clearInterval(poll); setRefreshing(false);
                  if (s?.error) setRefreshMsg(t('deck:refreshFailed'));
                  else { setRefreshMsg(t('deck:refreshDone', { count: s?.progress ?? 0 })); loadCardImages(); }
                }
              } catch { clearInterval(poll); setRefreshing(false); }
            }, 1500);
          } catch { setRefreshMsg(t('deck:refreshFailed')); setRefreshing(false); }
        }}
          disabled={refreshing || deckRefreshing}
          className="px-3 py-1.5 rounded-md bg-slate-800 border border-slate-700 text-slate-400 hover:text-sky-400 hover:border-sky-700/50 text-xs font-medium transition-colors disabled:opacity-50"
        >{refreshing ? t('deck:refreshing') : t('deck:refreshImages')}</button>
        {refreshing && <div className="flex items-center gap-1.5"><div className="w-16 h-1 bg-slate-700 rounded-full overflow-hidden"><div className="h-full bg-sky-500 transition-all duration-500" style={{width:`${progress}%`}}/></div><span className="text-[10px] text-slate-500 font-mono">{progress}%</span></div>}
        {!refreshing && refreshMsg && <span className="text-[11px] text-slate-500">{refreshMsg}</span>}
      </div>
      {/* Grid or loading skeleton */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-60 rounded-xl bg-slate-900 border border-slate-800 animate-pulse" />
          ))}
        </div>
      ) : decks.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-slate-600">
          <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="mb-4 opacity-40">
            <rect x="2" y="5" width="20" height="14" rx="2" /><path d="M2 10h20" />
          </svg>
          <p className="text-sm font-medium">{t('deck:noDecks')}</p>
          <p className="text-xs mt-1 font-mono text-slate-700">{t('deck:createFirstDeck')}</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {decks.map(deck => (
            <DeckCard key={deck.id} deck={deck} cardImages={cardImages} onPlay={onPlayWithDeck} onClick={setDetailDeckId} />
          ))}
        </div>
      )}

      <DeckDetailModal
        deckId={detailDeckId ?? ''}
        isOpen={detailDeckId !== null}
        onClose={() => setDetailDeckId(null)}
      />
    </div>
  );
}
