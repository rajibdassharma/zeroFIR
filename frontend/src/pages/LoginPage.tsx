import { useState } from 'react';
import { useNavigate } from 'react-router';
import { toast } from 'sonner';
import { login } from '../lib/api/auth';

/** Placeholder login form (Phase 0). Phase 1 will swap this for the
 *  District → PS → User ID dropdown chain (same shape as CyberFraud's
 *  hardened LoginForm — no free-text usernames on production). */
export function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    try {
      const res = await login(username, password);
      toast.success(`Signed in as ${res.role}`);
      navigate('/');
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4" style={{ background: 'var(--ksp-navy)' }}>
      <form
        onSubmit={handleSubmit}
        className="rounded-2xl p-8 max-w-sm w-full space-y-4"
        style={{ background: '#fff', border: '3px solid var(--ksp-yellow)' }}
      >
        <h1 className="text-2xl font-bold" style={{ color: 'var(--ksp-navy)' }}>
          zeroFIR
        </h1>
        <p className="text-xs italic" style={{ color: 'var(--ksp-red)' }}>
          Karnataka State Police · Zero FIR Tracking
        </p>

        <div>
          <label className="block text-sm font-semibold mb-1">Username</label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            autoComplete="username"
            className="w-full px-4 py-2 rounded-xl text-sm outline-none"
            style={{ border: '2px solid var(--ksp-navy)' }}
          />
        </div>

        <div>
          <label className="block text-sm font-semibold mb-1">Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
            className="w-full px-4 py-2 rounded-xl text-sm outline-none"
            style={{ border: '2px solid var(--ksp-navy)' }}
          />
        </div>

        <button
          type="submit"
          disabled={busy || !username || !password}
          className="w-full py-2 font-bold rounded-xl disabled:opacity-50"
          style={{ background: 'var(--ksp-yellow)', color: '#000' }}
        >
          {busy ? 'Signing in…' : 'Sign In'}
        </button>
      </form>
    </div>
  );
}
