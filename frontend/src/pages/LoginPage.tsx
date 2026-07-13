import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router';
import { toast } from 'sonner';
import { login } from '../lib/api/auth';
import {
  listDistricts,
  listPoliceStations,
  listSuperAdmins,
  listUsersForPS,
} from '../lib/api/master';
import { setToken } from '../lib/api/client';
import { useAuth } from '../lib/stores/auth-store';
import type { District, PoliceStation, UserOption } from '../types';

type LoginPath = 'ps' | 'super_admin';

/** District → PS → User ID dropdown chain — CyberFraud shape.
 *  Free-text usernames are a security anti-pattern; every user picks
 *  from a scoped list and enters just the password. `super_admin`
 *  bypasses the District/PS pickers via a dedicated toggle. */
export function LoginPage() {
  const navigate = useNavigate();
  const setUser = useAuth((s) => s.setUser);

  const [path, setPath] = useState<LoginPath>('ps');
  const [districts, setDistricts] = useState<District[]>([]);
  const [districtId, setDistrictId] = useState<number | ''>('');
  const [pses, setPSes] = useState<PoliceStation[]>([]);
  const [psId, setPSId] = useState<number | ''>('');
  const [users, setUsers] = useState<UserOption[]>([]);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);

  // Districts on mount, super_admins on toggle.
  useEffect(() => {
    if (path === 'ps') {
      listDistricts()
        .then(setDistricts)
        .catch((e) => toast.error(e.message));
    } else {
      listSuperAdmins()
        .then(setUsers)
        .catch((e) => toast.error(e.message));
    }
  }, [path]);

  // PS list when district changes.
  useEffect(() => {
    if (typeof districtId !== 'number') {
      setPSes([]); setPSId(''); setUsers([]); setUsername('');
      return;
    }
    listPoliceStations(districtId)
      .then((ps) => { setPSes(ps); setPSId(''); setUsers([]); setUsername(''); })
      .catch((e) => toast.error(e.message));
  }, [districtId]);

  // User list when PS changes.
  useEffect(() => {
    if (typeof psId !== 'number') { setUsers([]); setUsername(''); return; }
    listUsersForPS(psId)
      .then((u) => { setUsers(u); setUsername(''); })
      .catch((e) => toast.error(e.message));
  }, [psId]);

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
        <h1 className="text-2xl font-bold" style={{ color: 'var(--ksp-navy)' }}>
          zeroFIR
        </h1>
        <p className="text-xs italic" style={{ color: 'var(--ksp-red)' }}>
          Karnataka State Police · Masking Application
        </p>

        {/* Login-path toggle */}
        <div className="flex gap-2 text-sm">
          <button
            type="button"
            onClick={() => setPath('ps')}
            className="flex-1 py-1 rounded-lg font-semibold"
            style={{
              background: path === 'ps' ? 'var(--ksp-navy)' : '#eee',
              color: path === 'ps' ? '#fff' : '#333',
            }}
          >
            PS User
          </button>
          <button
            type="button"
            onClick={() => setPath('super_admin')}
            className="flex-1 py-1 rounded-lg font-semibold"
            style={{
              background: path === 'super_admin' ? 'var(--ksp-navy)' : '#eee',
              color: path === 'super_admin' ? '#fff' : '#333',
            }}
          >
            Super Admin
          </button>
        </div>

        {path === 'ps' && (
          <>
            <div>
              <label className="block text-sm font-semibold mb-1">District</label>
              <select
                value={districtId}
                onChange={(e) => setDistrictId(e.target.value ? Number(e.target.value) : '')}
                required
                className="w-full px-3 py-2 rounded-xl text-sm bg-white"
                style={{ border: '2px solid var(--ksp-navy)' }}
              >
                <option value="">— Select district —</option>
                {districts.map((d) => (
                  <option key={d.id} value={d.id}>{d.name}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-semibold mb-1">Police Station</label>
              <select
                value={psId}
                onChange={(e) => setPSId(e.target.value ? Number(e.target.value) : '')}
                required
                disabled={pses.length === 0}
                className="w-full px-3 py-2 rounded-xl text-sm bg-white disabled:opacity-50"
                style={{ border: '2px solid var(--ksp-navy)' }}
              >
                <option value="">— Select PS —</option>
                {pses.map((p) => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            </div>
          </>
        )}

        <div>
          <label className="block text-sm font-semibold mb-1">User ID</label>
          <select
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            disabled={users.length === 0}
            className="w-full px-3 py-2 rounded-xl text-sm bg-white disabled:opacity-50"
            style={{ border: '2px solid var(--ksp-navy)' }}
          >
            <option value="">— Select user —</option>
            {users.map((u) => (
              <option key={u.username} value={u.username}>
                {u.username} ({u.role})
              </option>
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
