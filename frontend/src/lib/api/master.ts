import type { PoliceStation, UserOption } from '../../types';
import { apiFetch } from './client';

export function listCallCenterUsers() {
  return apiFetch<UserOption[]>('/api/v1/users/call-center/public');
}

export function listPoliceStations() {
  return apiFetch<PoliceStation[]>('/api/v1/police-stations/public');
}
