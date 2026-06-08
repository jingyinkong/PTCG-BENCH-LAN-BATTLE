import { useState, useEffect, useCallback } from 'react';
import { useAuthStore } from '../stores/authStore';
import { api } from '../services/api';

interface Issue { id: number; game_id: number; task_id: number; severity: string; category: string; error_signature: string; fingerprint_hash: string; status: string; created_at: string; }
interface IssueSummary { fingerprint: string; signature: string; category: string; severity: string; count: number; status: string; }

const STATUS_MAP: Record<string, string> = { pending: '待审', confirmed: '已确认', false_positive: '误报', duplicate: '重复' };
const SEVERITY_MAP: Record<string, string> = { confirmed: '🔴 确定', suspicious: '🟡 可疑' };
const CATEGORY_MAP: Record<string, string> = {
  state_check: '状态检查', engine_error: '引擎错误', softlock: '疑似死锁',
  zero_damage_win: '零伤害获胜', llm_anomaly: 'LLM 异常', rare_interaction: '罕见交互'
};

export default function IssueReview() {
  const { isAdmin } = useAuthStore();
  const [issues, setIssues] = useState<Issue[]>([]);
  const [summary, setSummary] = useState<IssueSummary[]>([]);
  const [selected, setSelected] = useState<Issue | null>(null);
  const [detail, setDetail] = useState<any>(null);
  const [filter, setFilter] = useState('');

  const fetchData = useCallback(async () => {
    try {
      const s = await api.getIssueSummary(); setSummary(s?.summary || []);
      const i = await api.listIssues({ status: filter || undefined }); setIssues(i?.issues || []);
    } catch {}
  }, [filter]);

  useEffect(() => { if (isAdmin) fetchData(); }, [isAdmin, fetchData]);

  const handleSelect = async (issue: Issue) => {
    setSelected(issue);
    try { setDetail(await api.getIssue(issue.id)); } catch { setDetail(null); }
  };

  const handleMark = async (status: string) => {
    if (!selected) return;
    try { await api.markIssue(selected.id, { status }); fetchData(); setDetail(null); setSelected(null); } catch {}
  };

  if (!isAdmin) return <div className="p-8 text-slate-400">需要管理员权限</div>;

  return (
    <div className="p-6 max-w-6xl mx-auto flex gap-4" style={{ height: 'calc(100vh - 100px)' }}>
      <div className="w-1/3 bg-slate-900 border border-slate-700 rounded-lg p-3 overflow-auto">
        <h2 className="text-lg font-bold text-slate-50 mb-3">检测到的问题</h2>
        <div className="flex gap-2 mb-3">
          {[['', '全部'], ['pending', '待审'], ['confirmed', '已确认'], ['false_positive', '误报']].map(([s, label]) => (
            <button key={s} onClick={() => setFilter(s)}
              className={`px-2 py-1 rounded text-xs ${filter === s ? 'bg-sky-600 text-white' : 'bg-slate-800 text-slate-400'}`}>{label}</button>))}
        </div>
        {summary.map(s => (
          <button key={s.fingerprint} onClick={() => handleSelect(issues.find(i => i.fingerprint_hash === s.fingerprint)!)}
            className="w-full text-left bg-slate-800 hover:bg-slate-700 rounded p-2 mb-1 text-xs">
            <div className="flex justify-between">
              <span className={`font-medium ${s.severity === 'confirmed' ? 'text-red-400' : 'text-amber-400'}`}>
                {CATEGORY_MAP[s.category] || s.category}</span>
              <span className="text-slate-500">×{s.count}</span>
            </div>
            <div className="text-slate-400 truncate">{s.signature?.slice(0, 80)}</div>
          </button>))}
        {summary.length === 0 && <p className="text-slate-500 text-xs p-4">暂无检测到的问题。</p>}
      </div>
      <div className="flex-1 bg-slate-900 border border-slate-700 rounded-lg p-4 overflow-auto">
        {!selected ? <p className="text-slate-500 text-sm text-center mt-20">选择一个问题查看详情</p> : (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-slate-50">{CATEGORY_MAP[selected.category] || selected.category}</h3>
              <span className={`px-2 py-0.5 rounded text-xs ${selected.severity === 'confirmed' ? 'bg-red-900/50 text-red-400' : 'bg-amber-900/50 text-amber-400'}`}>
                {SEVERITY_MAP[selected.severity] || selected.severity}</span>
            </div>
            <div className="bg-slate-800 rounded p-3 mb-3">
              <p className="text-sm text-slate-300">{selected.error_signature}</p>
              <p className="text-xs text-slate-500 mt-1">对局 #{selected.game_id} · 任务 #{selected.task_id} · 状态: {STATUS_MAP[selected.status] || selected.status}</p>
            </div>
            {detail?.state_snapshot && (
              <div className="mb-3">
                <h4 className="text-xs font-semibold text-slate-400 mb-1">状态快照</h4>
                <pre className="bg-slate-950 rounded p-2 text-xs text-slate-300 overflow-auto max-h-64">{JSON.stringify(detail.state_snapshot, null, 2)}</pre>
              </div>
            )}
            {detail?.last_n_actions && (
              <div className="mb-3">
                <h4 className="text-xs font-semibold text-slate-400 mb-1">最后操作序列</h4>
                <pre className="bg-slate-950 rounded p-2 text-xs text-slate-300 overflow-auto max-h-48">{JSON.stringify(detail.last_n_actions, null, 2)}</pre>
              </div>
            )}
            <div className="flex gap-2 mt-4">
              <button onClick={() => handleMark('confirmed')}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-sm font-semibold">✅ 确认为 Bug</button>
              <button onClick={() => handleMark('false_positive')}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded text-sm">❌ 标记误报</button>
              <button onClick={() => handleMark('duplicate')}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded text-sm">🔄 重复问题</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
