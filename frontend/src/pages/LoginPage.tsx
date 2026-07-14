import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router';
import { toast } from 'sonner';
import kspLogo from '../assets/ksp_logo.png';
import { login } from '../lib/api/auth';
import { listCallCenterUsers } from '../lib/api/master';
import { setToken } from '../lib/api/client';
import { useAuth } from '../lib/stores/auth-store';
import type { UserOption } from '../types';

/** Login — one form for one role. Every user of this app is a Call
 *  Centre operator (state-wide, centralised call centre); no
 *  super_admin, no PS-user login path. Operator picks their username
 *  from a scoped dropdown and enters just the password — no
 *  free-text usernames anywhere. */
export function LoginPage() {
  const navigate = useNavigate();
  const setUser = useAuth((s) => s.setUser);

  const [users, setUsers] = useState<UserOption[]>([]);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    listCallCenterUsers()
      .then(setUsers)
      .catch((e) => toast.error(e.message));
  }, []);

  const canSubmit = username.length > 0 && password.length > 0;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;
    setBusy(true);
    try {
      const res = await login(username, password);
      setToken(res.token);
      setUser({ user_id: res.user_id, role: res.role, full_name: res.full_name });
      toast.success(`Welcome, ${res.full_name ?? res.role}`);
      navigate('/complaints');
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div
      className="min-h-screen flex items-center justify-center px-4"
      style={{ background: 'var(--ksp-navy)' }}
    >
      <form
        onSubmit={handleSubmit}
        className="rounded-2xl p-8 max-w-md w-full space-y-4"
        style={{ background: '#fff', border: '3px solid var(--ksp-yellow)' }}
      >
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl" style={{ background: 'rgba(11,44,74,0.05)' }}>
            <img src={kspLogo} alt="KSP Logo" className="w-14 h-14 object-contain" />
          </div>
          <div>
            <h1 className="text-2xl font-bold" style={{ color: 'var(--ksp-navy)' }}>
              zeroFIR
            </h1>
            <p className="text-xs italic" style={{ color: 'var(--ksp-red)' }}>
              Karnataka State Police · Call-Centre Masking Application
            </p>
          </div>
        </div>

        <div>
          <label className="block text-sm font-semibold mb-1">Operator ID</label>
          <select
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            disabled={users.length === 0}
            className="w-full px-3 py-2 rounded-xl text-sm bg-white disabled:opacity-50"
            style={{ border: '2px solid var(--ksp-navy)' }}
          >
            <option value="">— Select operator —</option>
            {users.map((u) => (
              <option key={u.username} value={u.username}>{u.username}</option>
            ))}
          </select>
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
          disabled={busy || !canSubmit}
          className="w-full py-2 font-bold rounded-xl disabled:opacity-50"
          style={{ background: 'var(--ksp-yellow)', color: '#000' }}
        >
          {busy ? 'Signing in…' : 'Sign In'}
        </button>
      </form>
    </div>
  );
}
