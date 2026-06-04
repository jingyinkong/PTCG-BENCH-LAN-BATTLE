import { useState, useEffect } from 'react';
import { api, MatchRecord, MatchStats } from '../services/api';

export default function MatchHistory() {
  const [records, setRecords] = useState<MatchRecord[]>([]);
  const [stats, setStats] = useState<MatchStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [recData, statData] = await Promise.all([
          api.getMatchRecords(20, 0),
          api.getMatchStats(),
        ]);
        setRecords(recData.records);
        setStats(statData);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center" style={{ minHeight: 'calc(100vh - 44px)' }}>
        <p className="text-slate-400">Loading...</p>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-3xl mx-auto" style={{ minHeight: 'calc(100vh - 44px)' }}>
      <h2 className="text-2xl font-bold text-slate-50 mb-6">Battle History</h2>

      {/* Stats cards */}
      {stats && (
        <div className="grid grid-cols-4 gap-3 mb-8">
          <div className="bg-slate-900 border border-slate-700 rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-sky-400">{stats.total_games}</div>
            <div className="text-xs text-slate-500 mt-1">Games</div>
          </div>
          <div className="bg-slate-900 border border-slate-700 rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-emerald-400">{stats.wins}</div>
            <div className="text-xs text-slate-500 mt-1">Wins</div>
          </div>
          <div className="bg-slate-900 border border-slate-700 rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-red-400">{stats.losses}</div>
            <div className="text-xs text-slate-500 mt-1">Losses</div>
          </div>
          <div className="bg-slate-900 border border-slate-700 rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-amber-400">{(stats.win_rate * 100).toFixed(0)}%</div>
            <div className="text-xs text-slate-500 mt-1">Win Rate</div>
          </div>
        </div>
      )}

      {/* Records table */}
      {records.length === 0 ? (
        <p className="text-center text-slate-500 py-8">No battles recorded yet</p>
      ) : (
        <div className="bg-slate-900 border border-slate-700 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-700 text-slate-400 text-xs">
                <th className="text-left px-4 py-2">Opponent</th>
                <th className="text-left px-4 py-2">Decks</th>
                <th className="text-center px-4 py-2">Result</th>
                <th className="text-right px-4 py-2">Date</th>
              </tr>
            </thead>
            <tbody>
              {records.map((r) => {
                return (
                  <tr key={r.id} className="border-b border-slate-800 last:border-0">
                    <td className="px-4 py-3 text-slate-200">
                      {r.player1_name} vs {r.player2_name}
                    </td>
                    <td className="px-4 py-3 text-slate-400 text-xs">
                      {r.deck1_name || '?'} vs {r.deck2_name || '?'}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`text-xs font-medium px-2 py-0.5 rounded ${
                        r.winner_name ? 'text-emerald-400' : 'text-slate-500'
                      }`}>
                        {r.winner_name ? `W — ${r.winner_name}` : 'Draw'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-500 text-xs text-right">
                      {r.played_at ? new Date(r.played_at).toLocaleDateString() : '—'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
