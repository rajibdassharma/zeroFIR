import type { ReactNode } from 'react';
import { Navigate } from 'react-router';
import { getToken } from '../lib/api/client';

/** Route gate — if there's no bearer token, punt to /login. */
export function RequireAuth({ children }: { children: ReactNode }) {
  if (!getToken()) return <Navigate to="/login" replace />;
  return <>{children}</>;
}
