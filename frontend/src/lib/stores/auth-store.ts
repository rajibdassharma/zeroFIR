import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { SessionUser } from '../../types';

interface AuthState {
  user: SessionUser | null;
  setUser: (u: SessionUser | null) => void;
  logout: () => void;
}

/** Cheap client-side cache of the logged-in user. The bearer token
 *  itself lives in localStorage via `client.setToken`; this store
 *  just holds the shape needed to render the header + gate routes. */
export const useAuth = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      setUser: (u) => set({ user: u }),
      logout: () => set({ user: null }),
    }),
    { name: 'zerofir_session' },
  ),
);
