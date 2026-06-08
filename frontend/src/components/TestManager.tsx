import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuthStore } from '../stores/authStore';
import { api } from '../services/api';

interface TestTask {
  id: number; status: string; deck_list: string[];
  agent_config: any[]; batch_size: number; max_budget: number | null;
  game_count: number; created_at: string;
}

interface ApiKeyStatus {
  provider: string; configured: boolean; masked_key: string;
}

const AGENT_TYPES = [
  { value: 'random', label: '随机', needsModel: false },
  { value: 'charizard_heuristic', label: '喷火龙规则', needsModel: false },
  { value: 'react', label: 'ReAct (LLM)', needsModel: true },
  { value: 'skillevolving', label: '技能进化 (LLM)', needsModel: true },
];

const DECKS = ['charizard_ex', 'gardevori_ex', 'gholdengo_ex', 'lugia_archeops', 'miraidon_ex'];

const PROVIDER_LABELS: Record<string, string> = {
  deepseek: 'DeepSeek', openrouter: 'OpenRouter', zai: '智谱 (GLM)',
  dashscope: '阿里 (Qwen)', minimax: 'MiniMax',
};

export default function TestManager() {
  const { t } = useTranslation(['test', 'common']);
  const { isAdmin } = useAuthStore();
  const [tasks, setTasks] = useState<TestTask[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedDecks, setSelectedDecks] = useState<string[]>(['charizard_ex']);
  const [agentConfigs, setAgentConfigs] = useState<any[]>([
    { type: 'random', model: '', player: 1 }, { type: 'random', model: '', player: 2 },
  ]);
  const [batchSize, setBatchSize] = useState(10);
  const [msg, setMsg] = useState('');

  const [apiKeys, setApiKeys] = useState<ApiKeyStatus[]>([]);
  const [editingProvider, setEditingProvider] = useState<string | null>(null);
  const [newKey, setNewKey] = useState('');
  const [showSettings, setShowSettings] = useState(false);

  const fetchApiKeys = useCallback(async () => {
    try { const r = await api.getApiKeys(); setApiKeys(r.providers || []); } catch {}
  }, []);

  const handleSaveKey = async (provider: string) => {
    try {
      await api.updateApiKey({ provider, api_key: newKey });
      fetchApiKeys(); setEditingProvider(null); setNewKey('');
      setMsg(`API ${PROVIDER_LABELS[provider] || provider} ${t('keyStatus.set')}`);
    } catch (e: any) { setMsg(e?.response?.data?.detail || t('test:failed')); }
  };

  const fetchTasks = useCallback(async () => {
    try { const r = await api.listTestTasks(); setTasks(r.tasks || []); } catch {}
  }, []);

  useEffect(() => { if (isAdmin) { fetchTasks(); fetchApiKeys(); } }, [isAdmin, fetchTasks, fetchApiKeys]);

  const handleStart = async () => {
    setLoading(true); setMsg('');
    try {
      const res = await api.createTestTask({ deck_list: selectedDecks, agent_configs: agentConfigs, batch_size: batchSize });
      setMsg(t('test:started', { id: res?.task_id })); fetchTasks();
    } catch (e: any) { setMsg(e?.response?.data?.detail || t('test:failed')); }
    setLoading(false);
  };

  if (!isAdmin) return <div className="p-8 text-slate-400">{t('test:adminRequired')}</div>;

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold text-slate-50 mb-6">{t('test:title')}</h2>
      {msg && <div className="mb-4 p-3 bg-sky-900/50 border border-sky-500/50 rounded text-sky-300 text-sm">{msg}</div>}

      {/* API Key Settings */}
      <div className="bg-slate-900 border border-slate-700 rounded-lg p-4 mb-4">
        <div className="flex items-center justify-between cursor-pointer" onClick={() => setShowSettings(!showSettings)}>
          <h3 className="text-sm font-semibold text-slate-300">{t('test:settings')}</h3>
          <span className="text-slate-500 text-xs">{showSettings ? '▲' : '▼'}</span>
        </div>
        {showSettings && (
          <div className="mt-3 space-y-2">
            {apiKeys.map(k => (
              <div key={k.provider} className="flex items-center gap-3 bg-slate-800 rounded p-2">
                <span className="text-xs text-slate-300 w-28">{PROVIDER_LABELS[k.provider] || k.provider}</span>
                <span className={`text-xs w-20 ${k.configured ? 'text-emerald-400' : 'text-slate-500'}`}>
                  {k.configured ? t('test:keyStatus.set') : t('test:keyStatus.notSet')}
                </span>
                {k.configured && <span className="text-xs text-slate-500 font-mono">{k.masked_key}</span>}
                {editingProvider === k.provider ? (
                  <div className="flex items-center gap-2 flex-1">
                    <input type="password" placeholder={t('test:keyActions.pasteHint')} value={newKey}
                      onChange={e => setNewKey(e.target.value)}
                      className="flex-1 bg-slate-900 border border-slate-600 rounded px-2 py-1 text-xs text-slate-200" />
                    <button onClick={() => handleSaveKey(k.provider)}
                      className="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs">{t('test:keyActions.save')}</button>
                    <button onClick={() => setEditingProvider(null)}
                      className="px-3 py-1 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded text-xs">{t('test:keyActions.cancel')}</button>
                  </div>
                ) : (
                  <button onClick={() => { setEditingProvider(k.provider); setNewKey(''); }}
                    className="px-3 py-1 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded text-xs">
                    {k.configured ? t('test:keyActions.update') : t('test:keyActions.setKey')}
                  </button>
                )}
              </div>
            ))}
            <p className="text-xs text-slate-500 mt-2">{t('test:keyHint')}</p>
          </div>
        )}
      </div>

      {/* New Test Run */}
      <div className="bg-slate-900 border border-slate-700 rounded-lg p-4 mb-6">
        <h3 className="text-sm font-semibold text-slate-300 mb-3">{t('test:newRun')}</h3>
        <div className="mb-3">
          <label className="text-xs text-slate-400 mb-1 block">{t('test:decks')}</label>
          <div className="flex flex-wrap gap-2">
            {DECKS.map(d => (
              <button key={d} onClick={() => setSelectedDecks(p => p.includes(d) ? p.filter(x => x !== d) : [...p, d])}
                className={`px-3 py-1 rounded text-xs font-medium ${selectedDecks.includes(d) ? 'bg-sky-600 text-white' : 'bg-slate-800 text-slate-400 border border-slate-700'}`}>{d}</button>
            ))}
          </div>
        </div>
        <div className="mb-3 grid grid-cols-2 gap-3">
          {agentConfigs.map((a, i) => (
            <div key={i} className="bg-slate-800 rounded p-2">
              <label className="text-xs text-slate-400">{t('test:playerAgent', { n: a.player })}</label>
              <select value={a.type} onChange={e => setAgentConfigs(p => p.map((x, j) => j === i ? {...x, type: e.target.value} : x))}
                className="w-full mt-1 bg-slate-900 border border-slate-700 rounded px-2 py-1 text-sm text-slate-200">
                {AGENT_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
              </select>
              {AGENT_TYPES.find(t => t.value === a.type)?.needsModel && (
                <input placeholder="模型名称 (如 deepseek-chat)" value={a.model}
                  onChange={e => setAgentConfigs(p => p.map((x, j) => j === i ? {...x, model: e.target.value} : x))}
                  className="w-full mt-1 bg-slate-900 border border-slate-700 rounded px-2 py-1 text-sm text-slate-200" />
              )}
            </div>
          ))}
        </div>
        <div className="flex items-center gap-4">
          <div><label className="text-xs text-slate-400 block">{t('test:batchSize')}</label>
            <input type="number" value={batchSize} onChange={e => setBatchSize(Number(e.target.value))} min={1} max={100}
              className="w-24 bg-slate-800 border border-slate-700 rounded px-2 py-1 text-sm text-slate-200" /></div>
          <button onClick={handleStart} disabled={loading || selectedDecks.length === 0}
            className="mt-4 px-6 py-2 bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white rounded-lg font-semibold text-sm">
            {loading ? t('test:starting') : t('test:startTest')}</button>
        </div>
      </div>

      {/* Task History */}
      <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-slate-300 mb-3">{t('test:taskHistory')}</h3>
        {tasks.length === 0 ? <p className="text-slate-500 text-sm">{t('test:noTasks')}</p> : (
          <div className="space-y-2">{tasks.map(task => (
            <div key={task.id} className="flex items-center justify-between bg-slate-800 rounded p-3 text-sm">
              <div><span className="text-slate-200 font-medium">{t('test:taskLabel', { id: task.id })}</span>
                <span className="ml-3 text-xs text-slate-500">{task.deck_list?.join(', ')} · {t('test:gameCount', { count: task.batch_size })}</span></div>
              <div className="flex items-center gap-3">
                <span className="text-xs text-slate-400">{task.created_at?.slice(0, 16)}</span>
                <span className={`px-2 py-0.5 rounded text-xs ${task.status === 'completed' ? 'bg-emerald-900/50 text-emerald-400' : task.status === 'running' ? 'bg-sky-900/50 text-sky-400' : task.status === 'failed' ? 'bg-red-900/50 text-red-400' : 'bg-slate-700 text-slate-400'}`}>
                  {(['completed','running','failed','pending','cancelled'].includes(task.status) ? t(`test:status.${task.status}`) : task.status)}</span>
                <span className="text-xs text-slate-500">{t('test:gameCount', { count: task.game_count })}</span></div></div>))}</div>)}
      </div>
    </div>
  );
}
