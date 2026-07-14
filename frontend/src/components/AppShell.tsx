import type { ReactNode } from 'react';
import { Link, useNavigate } from 'react-router';
import kspLogo from '../assets/ksp_logo.png';
import { setToken } from '../lib/api/client';
import { useAuth } from '../lib/stores/auth-store';

/** Minimal chrome around every authenticated page. Same feel as
 *  CyberFraud: KSP header bar + inline logout, no sidebar yet. */
export function AppShell({ children }: { children: ReactNode }) {
  const user = useAuth((s) => s.user);
  const logout = useAuth((s) => s.logout);
  const navigate = useNavigate();

  const handleLogout = () => {
    setToken(null);
    logout();
    navigate('/login', { replace: true });
  };

  return (
    <div className="min-h-screen" style={{ background: '#f5f5f7' }}>
      <header
        className="flex items-center justify-between px-6 py-3"
        style={{ background: 'var(--ksp-navy)', color: '#fff' }}
      >
        <Link to="/complaints" className="flex items-center gap-3">
          <span
            className="inline-flex items-center justify-center rounded-lg p-1"
            style={{ background: 'rgba(255,255,255,0.9)' }}
          >
            <img src={kspLogo} alt="KSP Logo" className="w-9 h-9 object-contain" />
          </span>
          <span className="flex flex-col leading-tight">
            <span className="text-xl font-bold">zeroFIR</span>
            <span className="text-xs opacity-80">Masking Application · Karnataka State Police</span>
          </span>
        </Link>
        <nav className="flex items-center gap-4 text-sm">
          <Link to="/complaints" className="hover:underline">Complaints</Link>
          {user && (
            <>
              <span className="opacity-80">
                {user.full_name ?? user.role} · {user.role}
              </span>
              <button
                type="button"
                onClick={handleLogout}
                className="px-3 py-1 rounded-lg font-semibold text-xs"
                style={{ background: 'var(--ksp-yellow)', color: '#000' }}
              >
                Log out
              </button>
            </>
          )}
        </nav>
      </header>
      <main className="p-6">{children}</main>
    </div>
  );
}
