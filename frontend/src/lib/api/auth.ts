import { apiFetch, setToken } from './client';

export interface LoginResponse {
  token: string;
  role: string;
  user_id: number;
  full_name: string | null;
  must_change_password: boolean;
}

export async function login(username: string, password: string): Promise<LoginResponse> {
  const res = await apiFetch<LoginResponse>('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
  setToken(res.token);
  return res;
}
