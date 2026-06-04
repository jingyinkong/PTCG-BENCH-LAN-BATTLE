import { useState, useEffect } from 'react';
import { useAuthStore } from '../stores/authStore';

interface Props {
  onBack: () => void;
}

export default function AuthPage({ onBack }: Props) {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const { login, register, isLoading, error, clearError, isLoggedIn } = useAuthStore();

  // Redirect to home when login succeeds
  useEffect(() => {
    if (isLoggedIn) onBack();
  }, [isLoggedIn, onBack]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    if (!username || !password) return;
    if (username.length < 3 || username.length > 20) return;
    if (password.length < 6) return;
    if (mode === 'register') {
      if (password !== confirmPassword) return;
      const ok = await register(username, password);
      if (ok) setMode('login');
    } else {
      await login(username, password);
    }
  };

  return (
    <div className="flex items-center justify-center" style={{ minHeight: 'calc(100vh - 44px)' }}>
      <div className="bg-slate-900 border border-slate-700 rounded-xl p-8 w-full max-w-sm shadow-xl">
        <h2 className="text-xl font-bold text-slate-50 mb-6 text-center">
          {mode === 'login' ? 'Login' : 'Create Account'}
        </h2>
        <div className="flex mb-6 bg-slate-800 rounded-lg p-1">
          <button onClick={() => { setMode('login'); clearError(); }}
            className={`flex-1 py-1.5 rounded-md text-sm font-medium transition-colors ${mode === 'login' ? 'bg-sky-600 text-white' : 'text-slate-400 hover:text-slate-200'}`}>
            Login
          </button>
          <button onClick={() => { setMode('register'); clearError(); }}
            className={`flex-1 py-1.5 rounded-md text-sm font-medium transition-colors ${mode === 'register' ? 'bg-sky-600 text-white' : 'text-slate-400 hover:text-slate-200'}`}>
            Register
          </button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs text-slate-400 mb-1">Username</label>
            <input type="text" value={username} onChange={(e) => setUsername(e.target.value)}
              minLength={3} maxLength={20}
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 text-sm focus:outline-none focus:border-sky-500" placeholder="3-20 characters" />
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">Password</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
              minLength={6}
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 text-sm focus:outline-none focus:border-sky-500" placeholder="6+ characters" />
          </div>
          {mode === 'register' && (
            <div>
              <label className="block text-xs text-slate-400 mb-1">Confirm Password</label>
              <input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)}
                minLength={6}
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 text-sm focus:outline-none focus:border-sky-500" placeholder="Re-enter password" />
            </div>
          )}
          {error && (
            <div className="text-red-400 text-xs bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">{error}</div>
          )}
          <button type="submit" disabled={isLoading}
            className="w-full py-2.5 bg-sky-600 hover:bg-sky-500 disabled:bg-slate-700 text-white rounded-lg font-semibold text-sm transition-colors">
            {isLoading ? 'Loading...' : mode === 'login' ? 'Login' : 'Create Account'}
          </button>
        </form>
      </div>
    </div>
  );
}
